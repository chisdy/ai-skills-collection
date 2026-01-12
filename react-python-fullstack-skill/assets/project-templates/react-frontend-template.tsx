// React 前端项目模板
// 使用此模板快速搭建 React + TypeScript 项目结构

/*
项目结构:
src/
├── components/          # 共享 UI 组件
│   ├── ui/             # 基础 UI 组件 (shadcn/ui)
│   └── layout/         # 布局组件
├── features/           # 功能模块
│   ├── auth/
│   │   ├── components/ # 认证相关组件
│   │   ├── hooks/      # 认证相关 hooks
│   │   ├── types/      # 认证相关类型
│   │   └── api/        # 认证 API
│   └── users/
│       ├── components/
│       ├── hooks/
│       ├── types/
│       └── api/
├── hooks/              # 全局 hooks
├── lib/                # 工具库
│   ├── api.ts         # Axios 配置
│   ├── utils.ts       # 工具函数
│   └── validations.ts # Zod schemas
├── stores/             # Zustand 状态管理
├── types/              # 全局类型定义
└── App.tsx
*/

// ===== lib/api.ts =====
import axios, { AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// API 响应类型
export interface APIResponse<T> {
    success: boolean;
    data: T;
    message?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

// ===== types/user.ts =====
export interface UserBase {
    email: string;
    fullName: string;
    isActive: boolean;
}

export interface UserCreate extends UserBase {
    password: string;
}

export interface UserUpdate {
    email?: string;
    fullName?: string;
    isActive?: boolean;
    password?: string;
}

export interface UserResponse extends UserBase {
    id: number;
    createdAt: string;
    updatedAt?: string;
}

// ===== types/auth.ts =====
export interface LoginRequest {
    email: string;
    password: string;
}

export interface Token {
    accessToken: string;
    tokenType: string;
}

// ===== lib/validations.ts =====
import { z } from 'zod';

export const loginSchema = z.object({
    email: z.string().email('请输入有效的邮箱地址'),
    password: z.string().min(6, '密码至少需要6个字符'),
});

export const userCreateSchema = z.object({
    email: z.string().email('请输入有效的邮箱地址'),
    fullName: z.string().min(2, '姓名至少需要2个字符').max(100, '姓名不能超过100个字符'),
    password: z.string().min(6, '密码至少需要6个字符'),
    isActive: z.boolean().default(true),
});

export const userUpdateSchema = z.object({
    email: z.string().email('请输入有效的邮箱地址').optional(),
    fullName: z.string().min(2, '姓名至少需要2个字符').max(100, '姓名不能超过100个字符').optional(),
    isActive: z.boolean().optional(),
    password: z.string().min(6, '密码至少需要6个字符').optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type UserCreateFormData = z.infer<typeof userCreateSchema>;
export type UserUpdateFormData = z.infer<typeof userUpdateSchema>;

// ===== stores/authStore.ts =====
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserResponse } from '../types/user';

interface AuthState {
    user: UserResponse | null;
    token: string | null;
    isAuthenticated: boolean;
    setAuth: (user: UserResponse, token: string) => void;
    clearAuth: () => void;
    updateUser: (user: UserResponse) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            setAuth: (user, token) => {
                localStorage.setItem('access_token', token);
                set({ user, token, isAuthenticated: true });
            },
            clearAuth: () => {
                localStorage.removeItem('access_token');
                set({ user: null, token: null, isAuthenticated: false });
            },
            updateUser: (user) => set({ user }),
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                token: state.token,
                isAuthenticated: state.isAuthenticated
            }),
        }
    )
);

// ===== features/auth/api/authApi.ts =====
import { api } from '../../../lib/api';
import { LoginRequest, Token } from '../../../types/auth';
import { UserResponse } from '../../../types/user';

export const authApi = {
    login: async (credentials: LoginRequest): Promise<Token> => {
        const formData = new FormData();
        formData.append('username', credentials.email);
        formData.append('password', credentials.password);

        const response = await api.post<Token>('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    getCurrentUser: async (): Promise<UserResponse> => {
        const response = await api.get<UserResponse>('/users/me');
        return response.data;
    },

    logout: async (): Promise<void> => {
        await api.post('/auth/logout');
    },
};

// ===== features/auth/hooks/useAuth.ts =====
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';
import { LoginRequest } from '../../../types/auth';

export const useLogin = () => {
    const navigate = useNavigate();
    const { setAuth } = useAuthStore();

    return useMutation({
        mutationFn: authApi.login,
        onSuccess: async (tokenData) => {
            // 获取用户信息
            const user = await authApi.getCurrentUser();
            setAuth(user, tokenData.accessToken);
            toast.success('登录成功');
            navigate('/dashboard');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.message || '登录失败');
        },
    });
};

export const useLogout = () => {
    const navigate = useNavigate();
    const { clearAuth } = useAuthStore();
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: authApi.logout,
        onSuccess: () => {
            clearAuth();
            queryClient.clear();
            toast.success('已退出登录');
            navigate('/login');
        },
        onError: () => {
            // 即使 API 调用失败，也清除本地状态
            clearAuth();
            queryClient.clear();
            navigate('/login');
        },
    });
};

export const useCurrentUser = () => {
    const { isAuthenticated } = useAuthStore();

    return useQuery({
        queryKey: ['currentUser'],
        queryFn: authApi.getCurrentUser,
        enabled: isAuthenticated,
        staleTime: 5 * 60 * 1000, // 5分钟
        retry: false,
    });
};

// ===== features/auth/components/LoginForm.tsx =====
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { loginSchema, LoginFormData } from '../../../lib/validations';
import { useLogin } from '../hooks/useAuth';

export const LoginForm: React.FC = () => {
    const login = useLogin();

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
    });

    const onSubmit = (data: LoginFormData) => {
        login.mutate(data);
    };

    return (
        <Card className="w-full max-w-md mx-auto">
            <CardHeader>
                <CardTitle>登录</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">邮箱</Label>
                        <Input
                            id="email"
                            type="email"
                            {...register('email')}
                            className={errors.email ? 'border-red-500' : ''}
                        />
                        {errors.email && (
                            <p className="text-sm text-red-500">{errors.email.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password">密码</Label>
                        <Input
                            id="password"
                            type="password"
                            {...register('password')}
                            className={errors.password ? 'border-red-500' : ''}
                        />
                        {errors.password && (
                            <p className="text-sm text-red-500">{errors.password.message}</p>
                        )}
                    </div>

                    <Button
                        type="submit"
                        className="w-full"
                        disabled={isSubmitting || login.isPending}
                    >
                        {login.isPending ? '登录中...' : '登录'}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
};

// ===== features/users/api/usersApi.ts =====
import { api } from '../../../lib/api';
import { UserCreate, UserUpdate, UserResponse } from '../../../types/user';
import { PaginatedResponse } from '../../../lib/api';

export const usersApi = {
    getUsers: async (page = 1, size = 10): Promise<PaginatedResponse<UserResponse>> => {
        const response = await api.get<PaginatedResponse<UserResponse>>('/users/', {
            params: { page, size },
        });
        return response.data;
    },

    getUser: async (id: number): Promise<UserResponse> => {
        const response = await api.get<UserResponse>(`/users/${id}`);
        return response.data;
    },

    createUser: async (userData: UserCreate): Promise<UserResponse> => {
        const response = await api.post<UserResponse>('/users/', userData);
        return response.data;
    },

    updateUser: async (id: number, userData: UserUpdate): Promise<UserResponse> => {
        const response = await api.put<UserResponse>(`/users/${id}`, userData);
        return response.data;
    },

    deleteUser: async (id: number): Promise<void> => {
        await api.delete(`/users/${id}`);
    },
};

// ===== features/users/hooks/useUsers.ts =====
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { usersApi } from '../api/usersApi';
import { UserCreate, UserUpdate } from '../../../types/user';

export const useUsers = (page = 1, size = 10) => {
    return useQuery({
        queryKey: ['users', page, size],
        queryFn: () => usersApi.getUsers(page, size),
        staleTime: 5 * 60 * 1000,
    });
};

export const useUser = (id: number) => {
    return useQuery({
        queryKey: ['users', id],
        queryFn: () => usersApi.getUser(id),
        enabled: !!id,
    });
};

export const useCreateUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: usersApi.createUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            toast.success('用户创建成功');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.message || '创建用户失败');
        },
    });
};

export const useUpdateUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, userData }: { id: number; userData: UserUpdate }) =>
            usersApi.updateUser(id, userData),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            queryClient.setQueryData(['users', data.id], data);
            toast.success('用户更新成功');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.message || '更新用户失败');
        },
    });
};

export const useDeleteUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: usersApi.deleteUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            toast.success('用户删除成功');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.message || '删除用户失败');
        },
    });
};

// 无限滚动
export const useInfiniteUsers = () => {
    return useInfiniteQuery({
        queryKey: ['users', 'infinite'],
        queryFn: ({ pageParam = 1 }) => usersApi.getUsers(pageParam, 20),
        getNextPageParam: (lastPage) => {
            return lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined;
        },
        initialPageParam: 1,
    });
};

// ===== features/users/components/UserList.tsx =====
import React from 'react';
import { Button } from '../../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { useUsers, useDeleteUser } from '../hooks/useUsers';
import { UserResponse } from '../../../types/user';

interface UserCardProps {
    user: UserResponse;
    onEdit: (user: UserResponse) => void;
}

const UserCard: React.FC<UserCardProps> = ({ user, onEdit }) => {
    const deleteUser = useDeleteUser();

    const handleDelete = () => {
        if (window.confirm('确定要删除这个用户吗？')) {
            deleteUser.mutate(user.id);
        }
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <span>{user.fullName}</span>
                    <Badge variant={user.isActive ? 'default' : 'secondary'}>
                        {user.isActive ? '活跃' : '非活跃'}
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-gray-600 mb-4">{user.email}</p>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEdit(user)}
                    >
                        编辑
                    </Button>
                    <Button
                        variant="destructive"
                        size="sm"
                        onClick={handleDelete}
                        disabled={deleteUser.isPending}
                    >
                        {deleteUser.isPending ? '删除中...' : '删除'}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

export const UserList: React.FC = () => {
    const [page, setPage] = React.useState(1);
    const { data: usersData, isLoading, error } = useUsers(page, 10);

    const handleEdit = (user: UserResponse) => {
        // 实现编辑逻辑
        console.log('Edit user:', user);
    };

    if (isLoading) {
        return <div className="text-center py-8">加载中...</div>;
    }

    if (error) {
        return <div className="text-center py-8 text-red-500">加载失败</div>;
    }

    if (!usersData?.items.length) {
        return <div className="text-center py-8">暂无用户</div>;
    }

    return (
        <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {usersData.items.map((user) => (
                    <UserCard key={user.id} user={user} onEdit={handleEdit} />
                ))}
            </div>

            {/* 分页 */}
            <div className="flex justify-center gap-2">
                <Button
                    variant="outline"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                >
                    上一页
                </Button>
                <span className="flex items-center px-4">
                    第 {page} 页，共 {usersData.pages} 页
                </span>
                <Button
                    variant="outline"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= usersData.pages}
                >
                    下一页
                </Button>
            </div>
        </div>
    );
};

// ===== hooks/useErrorHandler.ts =====
import { toast } from 'sonner';

export const useErrorHandler = () => {
    return (error: any) => {
        if (error.response?.data?.message) {
            toast.error(error.response.data.message);
        } else if (error.message) {
            toast.error(error.message);
        } else {
            toast.error('操作失败，请稍后重试');
        }
    };
};

// ===== App.tsx =====
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';
import { LoginForm } from './features/auth/components/LoginForm';
import { UserList } from './features/users/components/UserList';
import { useAuthStore } from './stores/authStore';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuthStore();
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="min-h-screen bg-gray-50">
                    <Routes>
                        <Route path="/login" element={<LoginForm />} />
                        <Route
                            path="/dashboard"
                            element={
                                <ProtectedRoute>
                                    <div className="container mx-auto py-8">
                                        <h1 className="text-3xl font-bold mb-8">用户管理</h1>
                                        <UserList />
                                    </div>
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/" element={<Navigate to="/dashboard" />} />
                    </Routes>
                </div>
            </Router>
            <Toaster position="top-right" />
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    );
};

export default App;
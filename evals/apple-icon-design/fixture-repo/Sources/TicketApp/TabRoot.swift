import SwiftUI

struct TabRoot: View {
    var body: some View {
        TabView {
            ContentView()
                .tabItem { Label("Tickets", systemImage: "ticket") }
            WalletView()
                .tabItem { Label("Wallet", systemImage: "wallet.bifold") }
            ProfileView()
                .tabItem { Label("Me", systemImage: "person.crop.circle") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gearshape.fill") }
        }
    }
}

struct WalletView: View {
    var body: some View {
        VStack {
            Image(systemName: "creditcard.and.123")
                .font(.largeTitle)
            Text("No cards yet")
        }
    }
}

struct ProfileView: View { var body: some View { Text("Profile") } }
struct SettingsView: View { var body: some View { Text("Settings") } }

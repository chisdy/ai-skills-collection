import SwiftUI

struct ContentView: View {
    @State private var tickets: [Ticket] = []
    @State private var isFavorite = false

    var body: some View {
        NavigationStack {
            List(tickets) { ticket in
                HStack {
                    Image(systemName: "ticket.fill")
                        .resizable()
                        .frame(width: 22, height: 22)
                    VStack(alignment: .leading) {
                        Text(ticket.title).font(.headline)
                        Text(ticket.venue).font(.subheadline).foregroundColor(.secondary)
                    }
                    Spacer()
                    Image(systemName: "chevron.forward.2")
                }
            }
            .navigationTitle("Tickets")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        isFavorite.toggle()
                    } label: {
                        Image(systemName: isFavorite ? "heart.fill" : "heart")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: share) {
                        Image(systemName: "square.and.arrow.up.circle.fill")
                    }
                }
                ToolbarItem(placement: .topBarLeading) {
                    Button(action: scan) {
                        Image(systemName: "qrcode.viewfinder")
                            .font(.system(size: 22))
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: showInbox) {
                        Image(systemName: "tray.and.arrow.down.badge.clock")
                    }
                }
            }
        }
    }

    func share() {}
    func scan() {}
    func showInbox() {}
}

struct Ticket: Identifiable {
    let id = UUID()
    let title: String
    let venue: String
}

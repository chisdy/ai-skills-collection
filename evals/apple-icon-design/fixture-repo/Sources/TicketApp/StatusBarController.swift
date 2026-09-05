import AppKit

/// macOS companion: shows the next event countdown in the menu bar.
final class StatusBarController {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
    private let popover = NSPopover()

    init() {
        if let button = item.button {
            button.image = NSImage(named: "MenuBarIcon")
            button.action = #selector(togglePopover)
            button.target = self
        }
        popover.contentViewController = CountdownViewController()
    }

    @objc private func togglePopover() {
        if popover.isShown { popover.performClose(nil) }
        else if let b = item.button { popover.show(relativeTo: b.bounds, of: b, preferredEdge: .minY) }
    }

    func setAlert(_ on: Bool) {
        item.button?.image = NSImage(named: on ? "MenuBarIcon-Red" : "MenuBarIcon")
    }
}

final class CountdownViewController: NSViewController {}

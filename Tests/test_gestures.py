"""Run gesture logic against a recording touch backend using the installed Swift compiler."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
models = (root / 'PlayTools/Editor/Models/Elements/Element.swift').read_text()
models = models.replace('import GameController', 'import Foundation')
actions = (root / 'PlayTools/Controls/Backend/Action/PlayAction.swift').read_text()
actions = actions[actions.index('protocol Action'):actions.index('class DraggableButtonAction')]
stubs = r'''
import Foundation
import Dispatch
extension CGFloat {
    var absoluteX: CGFloat { self * 1000 }
    var absoluteY: CGFloat { self * 600 }
}
enum UITouch { enum Phase { case began, moved, ended } }
enum KeyCodeNames {
    static let defaultCode = -10
    static let keyCodes = [4: "A"]
}
enum PlayInput { static let touchQueue = DispatchQueue(label: "test.touches") }
enum ActionDispatcher {
    static func register(key: String, handler: @escaping (Bool) -> Void) {}
}
struct Event {
    let point: CGPoint
    let phase: UITouch.Phase
    let time: TimeInterval
    let tapCount: Int
}
enum Toucher {
    static var events: [Event] = []
    static func touchcam(point: CGPoint, phase: UITouch.Phase, tid: inout Int?,
                         actionName: String, keyName: String, tapCount: Int = 1) {
        if phase == .began {
            guard tid == nil else { return }
            tid = 1
        } else {
            guard tid != nil else { return }
        }
        events.append(Event(point: point, phase: phase,
                            time: ProcessInfo.processInfo.systemUptime, tapCount: tapCount))
        if phase == .ended { tid = nil }
    }
}
'''
checks = r'''
let transform = KeyModelTransform(size: 5, xCoord: 0.2, yCoord: 0.3)
let end = KeyModelTransform(size: 5, xCoord: 0.8, yCoord: 0.7)
let original = Button(keyCode: 4, keyName: "A", transform: transform)
let encoder = PropertyListEncoder()
let decoder = PropertyListDecoder()
let legacy = try encoder.encode(original)
let decoded = try decoder.decode(Button.self, from: legacy)
assert(decoded.gesture == nil && decoded.endTransform == nil)
for gesture in [ButtonGesture.swipe, .doubleTap] {
    let button = Button(keyCode: 4, keyName: "A", transform: transform,
                        gesture: gesture, endTransform: end)
    let loaded = try decoder.decode(Button.self, from: encoder.encode(button))
    assert(loaded.gesture == gesture && loaded.endTransform?.xCoord == 0.8)
}
func run(_ gesture: ButtonGesture, cancel: Bool = false) -> [Event] {
    let action = GestureButtonAction(data: Button(keyCode: 4, keyName: "A", transform: transform,
                                                  gesture: gesture, endTransform: end))
    PlayInput.touchQueue.sync {
        Toucher.events = []
        action.update(pressed: true)
        action.update(pressed: true) // Autorepeat must not start another gesture.
        action.update(pressed: false) // A short key press still completes the gesture.
    }
    if cancel { action.invalidate() }
    Thread.sleep(forTimeInterval: 0.4)
    return PlayInput.touchQueue.sync { Toucher.events }
}
let swipe = run(.swipe)
assert(swipe.count == 17)
assert(swipe.first?.phase == .began && swipe.last?.phase == .ended)
assert(swipe.first!.point.x == 200 && swipe.first!.point.y == 180)
assert(swipe.last!.point.x == 800 && swipe.last!.point.y == 420)
assert(swipe.last!.time - swipe.first!.time >= 0.25)
for pair in zip(swipe, swipe.dropFirst()) {
    assert(pair.1.point.x >= pair.0.point.x && pair.1.point.y >= pair.0.point.y)
}
let taps = run(.doubleTap)
assert(taps.map(\.phase) == [.began, .ended, .began, .ended])
assert(taps[2].tapCount == 2)
assert(taps[2].time - taps[1].time >= 0.05)
assert(taps.allSatisfy { $0.point.x == 200 && $0.point.y == 180 })
for gesture in [ButtonGesture.swipe, .doubleTap] {
    let cancelled = run(gesture, cancel: true)
    assert(cancelled.map(\.phase) == [.began, .ended])
}
let held = GestureButtonAction(data: Button(keyCode: 4, keyName: "A", transform: transform,
                                            gesture: .doubleTap))
PlayInput.touchQueue.sync { Toucher.events = []; held.update(pressed: true) }
Thread.sleep(forTimeInterval: 0.3)
PlayInput.touchQueue.sync { held.update(pressed: true) }
Thread.sleep(forTimeInterval: 0.3)
PlayInput.touchQueue.sync {
    assert(Toucher.events.count == 4)
    held.update(pressed: false)
    held.update(pressed: true)
}
Thread.sleep(forTimeInterval: 0.3)
PlayInput.touchQueue.sync { assert(Toucher.events.count == 8) }
print("PASS: legacy decoding, persistence, swipe timing/path, double tap, autorepeat and cancellation")
'''
with tempfile.TemporaryDirectory() as tmp:
    source = Path(tmp) / 'main.swift'
    source.write_text(models + stubs + actions + checks)
    binary = Path(tmp) / 'gesture-tests'
    subprocess.run(['swiftc', '-swift-version', '5', '-module-cache-path', tmp + '/cache',
                    str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

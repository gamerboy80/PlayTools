import GameController

// Data structure definition should match those in
// https://github.com/PlayCover/PlayCover/blob/develop/PlayCover/Model/Keymapping.swift
struct KeyModelTransform: Codable {
    var size: CGFloat
    var xCoord: CGFloat
    var yCoord: CGFloat
}

protocol BaseElement: Codable {
    var keyName: String { get set }
    var transform: KeyModelTransform { get set }
}

// controller buttons are indexed with names
enum ButtonGesture: String, Codable {
    case swipe
    case doubleTap
}

struct Button: BaseElement {
    var keyCode: Int
    var keyName: String
    var transform: KeyModelTransform
    var gesture: ButtonGesture?
    var endTransform: KeyModelTransform?
}

enum JoystickMode: Int, Codable {
    case FIXED
    case FLOATING
}

struct Joystick: BaseElement {
    static let defaultMode = JoystickMode.FIXED
    var upKeyCode: Int
    var rightKeyCode: Int
    var downKeyCode: Int
    var leftKeyCode: Int
    var keyName: String = "Keyboard"
    var transform: KeyModelTransform
    var mode: JoystickMode?
}

struct MouseArea: BaseElement {
    var keyName: String
    var transform: KeyModelTransform
    init(transform: KeyModelTransform) {
        self.transform = transform
        self.keyName = "Mouse"
    }
    init(keyName: String, transform: KeyModelTransform) {
        self.transform = transform
        self.keyName = keyName
    }
}

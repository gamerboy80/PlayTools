//
//  Button.swift
//  PlayTools
//
//  Created by 许沂聪 on 2023/12/25.
//

import Foundation

class ButtonModel: ControlModel<Button> {

    override init(data: Button) {
        super.init(data: data)
        self.setKey(code: data.keyCode, name: data.keyName)
    }

    func save() -> Button {
        data
    }

    override func setKey(code: Int, name: String) {
        var buttonData = data
        buttonData.keyCode = code
        buttonData.keyName = name
        data = buttonData
        let label = data.gesture == .doubleTap ? "\(data.keyName)\n2×" : data.keyName
        button.setTitle(label, for: UIControl.State.normal)
    }
}

class SwipeButtonModel: ButtonModel {
    private var endpoint: SwipeEndpointModel!
    private let arrow = CAShapeLayer()

    override init(data: Button) {
        super.init(data: data)
        let end = data.endTransform ?? data.transform
        endpoint = SwipeEndpointModel(data: Button(keyCode: data.keyCode, keyName: data.keyName, transform: end))
        endpoint.parent = self
        arrow.strokeColor = UIColor.systemYellow.cgColor
        arrow.fillColor = UIColor.systemYellow.cgColor
        arrow.lineWidth = 3
        button.accessibilityLabel = "Swipe from"
        endpoint.button.accessibilityLabel = "Swipe to"
        updateLabels()
    }

    func attach(to view: UIView) {
        view.layer.addSublayer(arrow)
        view.addSubview(endpoint.button)
        updateArrow()
    }

    private func updateLabels() {
        button.setTitle("\(data.keyName)\nFrom", for: .normal)
        endpoint?.button.setTitle("To", for: .normal)
    }

    override func setKey(code: Int, name: String) {
        super.setKey(code: code, name: name)
        updateLabels()
    }

    override func move(deltaY: CGFloat, deltaX: CGFloat) {
        super.move(deltaY: deltaY, deltaX: deltaX)
        updateArrow()
    }

    override func resize(down: Bool) {
        super.resize(down: down)
        updateArrow()
    }

    override func focus(_ focus: Bool) {
        super.focus(focus)
        if !focus { endpoint.focus(false) }
    }

    override func save() -> Button {
        data.endTransform = endpoint.data.transform
        return data
    }

    override func remove() {
        super.remove()
        endpoint.button.removeFromSuperview()
        arrow.removeFromSuperlayer()
    }

    func updateArrow() {
        let start = button.center
        let end = endpoint.button.center
        let angle = atan2(end.y - start.y, end.x - start.x)
        let tip = CGPoint(x: end.x - cos(angle) * endpoint.button.bounds.width / 2,
                          y: end.y - sin(angle) * endpoint.button.bounds.height / 2)
        let path = UIBezierPath()
        path.move(to: start)
        path.addLine(to: tip)
        path.move(to: CGPoint(x: tip.x - 14 * cos(angle - .pi / 6),
                             y: tip.y - 14 * sin(angle - .pi / 6)))
        path.addLine(to: tip)
        path.addLine(to: CGPoint(x: tip.x - 14 * cos(angle + .pi / 6),
                                y: tip.y - 14 * sin(angle + .pi / 6)))
        arrow.path = path.cgPath
    }
}

class SwipeEndpointModel: ControlModel<Button> {
    weak var parent: SwipeButtonModel?

    override func move(deltaY: CGFloat, deltaX: CGFloat) {
        super.move(deltaY: deltaY, deltaX: deltaX)
        parent?.updateArrow()
    }

    override func resize(down: Bool) {
        super.resize(down: down)
        parent?.updateArrow()
    }

    override func setKey(code: Int, name: String) {
        parent?.setKey(code: code, name: name)
    }
}

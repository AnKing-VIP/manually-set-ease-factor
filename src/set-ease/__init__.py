from typing import List

from aqt import mw
from aqt.browser import Browser
from aqt.gui_hooks import (
    browser_will_show_context_menu,
    reviewer_will_show_context_menu,
)
from aqt.qt import *
from aqt.reviewer import Reviewer

from .compat import setup_compat_aliases
from .consts import ANKI_VERSION
from .gui.menu import setup_menu

# not available in older Anki versions
try:
    from anki.cards import CardId
except:
    pass

setup_compat_aliases()
setup_menu()

act = None  # stores QAction so it doesn't get garbage collected


def on_browser_context_menu(browser: Browser, menu: QMenu):
    if ANKI_VERSION >= 45 and browser.table.is_notes_mode():
        return

    if not browser.selected_cards():
        return

    global act
    act = QAction(text="Set Ease Factor")

    def open_ease_edit_window():
        cids = browser.selected_cards()
        EaseEditWindow(cids).exec()

    act.triggered.connect(open_ease_edit_window)
    menu.addAction(act)


browser_will_show_context_menu.append(on_browser_context_menu)


def on_reviewer_context_menu(reviewer: Reviewer, menu: QMenu):

    global act
    act = QAction(text="Set Ease Factor")

    def open_ease_edit_window():
        cids = [reviewer.card.id]
        EaseEditWindow(cids).exec()

    act.triggered.connect(open_ease_edit_window)
    menu.addAction(act)


reviewer_will_show_context_menu.append(on_reviewer_context_menu)


class EaseEditWindow(QDialog):
    def __init__(self, cids: List["CardId"]):
        super().__init__()

        self.cids = cids

        self._setup()

    def _setup(self):
        self.setWindowTitle("Set Ease Factor")

        self.outer_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.main_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.btn_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.outer_layout.addLayout(self.main_layout)
        self.outer_layout.addLayout(self.btn_layout)
        self.setLayout(self.outer_layout)

        self.label = QLabel(
            text="The lower the ease, the more\nfrequently a card will appear."
        )
        self.main_layout.addWidget(self.label)
        self.main_layout.addSpacing(10)

        self.spin_box_layout = QHBoxLayout()
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(131)
        self.spin_box.setMaximum(10_000)
        self.spin_box.setSingleStep(10)
        self.spin_box.setMaximumWidth(100)
        if len(self.cids) == 1:
            self.spin_box.setValue(
                mw.col.get_card(self.cids[0]).factor // 10
            )  # // 10 because anki saves the factor with an extra zero
        self.spin_box_layout.addWidget(self.spin_box)
        self.main_layout.addLayout(self.spin_box_layout)
        self.main_layout.addSpacing(10)

        self.btn_layout.addStretch(0)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.setShortcut("Ctrl+Return")
        self.save_btn.clicked.connect(self._on_save)
        self.btn_layout.addWidget(self.save_btn)

    def _on_cancel(self):
        self.close()

    def _on_save(self):

        msg = f"Set Ease of {len(self.cids)} card to {self.spin_box.value()}"
        if ANKI_VERSION >= 45:
            undo_id = mw.col.add_custom_undo_entry(msg)
        else:
            mw.checkpoint(msg)

        for cid in self.cids:
            card = mw.col.get_card(cid)
            card.factor = (
                self.spin_box.value() * 10
            )  # * 10 because anki saves the factor with an extra zero

            if ANKI_VERSION >= 45:
                mw.col.update_card(card)
                mw.col.merge_undo_entries(undo_id)
            else:
                card.flush()

        self.close()

        mw.col.reset()
        if ANKI_VERSION >= 45:
            mw.update_undo_actions()
        else:
            mw.reset()

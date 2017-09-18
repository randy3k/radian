from prompt_toolkit.buffer import Buffer
from prompt_toolkit.application.current import get_app


class ModalBuffer(Buffer):

    def _change_prompt_mode(self, index, redraw=True):
        if index < len(self.history.modes):
            mode = self.history.modes[index]
            if mode:
                app = get_app()
                app.mp.prompt_mode = mode
                if redraw:
                    app._redraw()

    def history_forward(self, count=1):
        super(ModalBuffer, self).history_forward()
        self._change_prompt_mode(self.working_index)

    def history_backward(self, count=1):
        super(ModalBuffer, self).history_backward()
        self._change_prompt_mode(self.working_index)

    def _search(self, *args, **kwargs):
        result = super(ModalBuffer, self)._search(*args, **kwargs)
        if result:
            self._change_prompt_mode(result[0], redraw=False)
        return result

    def apply_search(self, *args, **kwargs):
        super(ModalBuffer, self).apply_search(*args, **kwargs)
        self._change_prompt_mode(self.working_index)

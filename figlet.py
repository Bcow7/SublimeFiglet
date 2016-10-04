# coding=utf-8
import os
import sublime
import sublime_plugin
import sys

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_PATH)


def add_comment(text, prefix, padding):
    reversed_prefix = prefix[::-1]
    max_width = get_max_line_length(text)
    horizontal_border = prefix + ((max_width + 2*padding)*prefix[-1]) + reversed_prefix

    # First row
    result = horizontal_border + '\n'
    # Content
    for line in text.split('\n')[:-1]:
        result += prefix+ padding*' ' + line + (max_width-len(line)+padding)*' ' + reversed_prefix + '\n'
    # Last row
    result += horizontal_border + prefix[0]

    return result


def figlet_text(text):
    import pyfiglet
    settings = sublime.load_settings("Preferences.sublime-settings")
    font = settings.get('figlet_font', 'standard')
    prefix = settings.get('figlet_comment_prefix', 'None')
    padding = settings.get('figlet_comment_padding', 4)

    width = get_width()

    result = pyfiglet.Figlet(font=font, width=width).renderText(text=text)

    # Strip trailing whitespace, because why not?
    if settings.get('figlet_no_trailing_spaces', True):
        result = '\n'.join((line.rstrip() for line in result.split('\n')))

    if prefix != 'None':
        result = add_comment(result, prefix, padding)

    return result[:len(result) - 1]


def get_width():
    # Return width to wrap at (or large number if wrapping not enabled)
    width = 1000000

    view_settings = sublime.active_window().active_view().settings()
    if view_settings.get('word_wrap'):
        output_width = view_settings.get('wrap_width')
        if output_width not in (None, 0):
            width = output_width

    return width


def get_max_line_length(text):
    return max(len(line) for line in text.split('\n'))


class FigletSelectFontCommand(sublime_plugin.WindowCommand):
    def run(self):
        import pyfiglet
        self.fonts = pyfiglet.FigletFont.getFonts()
        self.window.show_quick_panel(self.fonts, self.on_done)

    def on_done(self, index):
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("figlet_font", self.fonts[index])
        sublime.save_settings("Preferences.sublime-settings")


class FigletSelectCommentStyleCommand(sublime_plugin.WindowCommand):
    def run(self):
        # TODO : Add an 'Automatic' mode that use the good
        # prefix according to the langage of the document
        self.prefixes = ['None', '#', '//', '/*']
        self.window.show_quick_panel(self.prefixes, self.on_done)

    def on_done(self, index):
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set("figlet_comment_prefix", self.prefixes[index])
        sublime.save_settings("Preferences.sublime-settings")


class FigletTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        sel = view.sel()
        if len(sel) == 1 and sel[0].size() > 0:
            view.run_command('figlet_insert_text', {'text': None})
        else:
            self.window.show_input_panel("Text to Figletize:", "",
                                         self.on_done, None, None)

    def on_done(self, text):
        view = self.window.active_view()
        view.run_command('figlet_insert_text', {'text': text})


class FigletInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None):
        view = self.view
        sel = view.sel()

        if text is None:  # ... then grab selection
            if len(sel) != 1 or sel[0].size() == 0:
                return
            text = view.substr(sel[0])

        cursor = min(sel[0].a, sel[0].b)

        text = figlet_text(text)

        view.erase(edit, sel[0])
        view.insert(edit, cursor, text)
        sel.clear()
        sel.add(sublime.Region(cursor, cursor + len(text)))

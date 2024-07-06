import sublime
import sublime_plugin
import webbrowser

class RuMateCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		selections = self.view.sel()
		for region in selections:
			if not region.empty():
				selected_text = self.view.substr(region)
				url=f"http://rumate.tw1.su/talks/?a=new&q={selected_text}"
				# print(url)
				webbrowser.open(url)

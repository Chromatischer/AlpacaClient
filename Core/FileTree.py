import os

from textual import on
from textual.app import ComposeResult, App
from textual.containers import Container
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Tree, Static, Markdown, Placeholder, Button
from textual.widgets._tree import TreeNode, TreeDataType

class SelectFileMessage(Message):
    file_path: str

    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__()

class FileViewer(Screen):
    CSS = """
        FileViewer {
            background: #322d2d;
        
            #main{
                layout: vertical;
            }
            #markdown-container {
                height: 9fr;
            }
            
            /*Markdown {
                height: 100%;
            }*/
            #header {
                margin: 1;
                layout: horizontal;
                height: 1fr;
                align: center middle;
                text-align: center;
            }
            Button {
                align: center middle;
                text-align: center;
                height: 1fr;
                width: 1fr;
            }
            #short {
                width: 3fr;
            }
        }
    """
    CODETYPES = [[".py", "python"], [".html", "html"], [".css", "css"], [".js", "javascript"], [".ts", "typescript"], [".c", "c"], [".cpp", "cpp"], [".java", "java"]]

    # Show a single file, content output as a Markdown object
    file_path: str
    is_code: bool = False
    code_type: str

    def __init__(self, file_path: str):
        self.file_path = file_path
        for code_type in self.CODETYPES:
            if code_type[0] in file_path:
                self.is_code = True
                self.code_type = code_type[1]
        super().__init__()

    def load_from_file(self) -> str:
        if not os.path.isfile(f"{self.file_path}"):
            return ""
        with open(self.file_path) as f:
            return f.read().strip()

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            with Container(id="header"):
                yield Button("Back", disabled=False, id="back")
                yield Placeholder("File Viewer", id="short")
                yield Button("Use", disabled=False, id="use")
            pre = f"```{self.code_type}\n" if self.is_code else ""
            post = f"\n```" if self.is_code else ""
            with Container(id="markdown-container"):
                #yield Placeholder("File Viewer", id="Markdown")
                yield Markdown(f"{pre}{self.load_from_file()}{post}")

    @on(Button.Pressed)
    def on_button_press(self, message: Button.Pressed) -> None:
        if message.button.id == "back":
            self.app.pop_screen()
        elif message.button.id == "use":
            self.app.post_message(SelectFileMessage(self.file_path))

class FileTee(Tree):
    start_location: str # The file path to where the tree should start from
    FILETYPES: [str] = [".json", ".pdf", ".txt", ".md", ".py", ".html", ".css", ".js", ".ts", ".c", ".cpp", ".java"]

    def __init__(self, start_location: str):
        self.start_location = start_location
        super().__init__(label="File Tree")

    def recursive_tree(self, branch: TreeNode[str], start_location: str):
        for dir_name in os.listdir(start_location):
            if dir_name.startswith(".") or dir_name.startswith("__"):
                continue
            if os.path.isdir(os.path.join(start_location, dir_name)):
                new = branch.add(dir_name)
                self.recursive_tree(new, os.path.join(start_location, dir_name))
            else:
                if any([file_type in dir_name for file_type in self.FILETYPES]):
                    branch.add_leaf(dir_name, data=f"file\\{os.path.join(start_location, dir_name)}")

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("Root")
        # Start the tree from the start location iterate through the files and directories and add them to the tree
        tree.root.expand()
        self.recursive_tree(tree.root, self.start_location)
        yield tree

    @on(Tree.NodeSelected)
    def on_node_selected(self, message: Tree.NodeSelected):
        node = message.node
        data = str(node.data).split("\\")
        if data[0] == "file":
            self.app.push_screen(FileViewer(data[1]))

class TreeApp(App):
    def compose(self):
        yield FileTee("/Users/chromatischer/PycharmProjects/AI-Assist")

    @on(SelectFileMessage)
    def on_select_file_message(self, message: SelectFileMessage):
        self.app.pop_screen()

if __name__ == "__main__":
    app = TreeApp()
    app.run()
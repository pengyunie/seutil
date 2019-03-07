class Table:

    def __init__(self, big=False, font_size="small", align="center", caption="Default Table",
                 label="fig:table:default"):
        self.big = big
        self.font_size = font_size
        self.align = align
        self.caption = caption
        self.label = label

        self.tabular = ""
        self.content = list()

    def __str__(self):
        latex_str = ""

        latex_str += "% Auto Generated From senl.util.latex.Table\n"

        if not self.big:
            latex_str += "\\begin{table}\n"
        else:
            latex_str += "\\begin{table*}\n"

        latex_str += "\\begin{{{0}}}\n".format(self.font_size)
        latex_str += "\\begin{{{0}}}\n".format(self.align)

        latex_str += "\\caption{{{0}}}\n".format(self.caption)
        latex_str += "\\label{{{0}}}\n".format(self.label)

        latex_str += "\\begin{{tabular}}{{{0}}}\n".format(self.tabular)

        for line in self.content:
            if isinstance(line, str):
                latex_str += line + "\n"
            else:
                latex_str += " & ".join(line) + " \\\\\n"

        latex_str += "\\end{tabular}\n"

        latex_str += "\\end{{{0}}}\n".format(self.align)
        latex_str += "\\end{{{0}}}\n".format(self.font_size)

        if not self.big:
            latex_str += "\\end{table}\n"
        else:
            latex_str += "\\end{table*}\n"

        return latex_str

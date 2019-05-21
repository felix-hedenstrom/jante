"""
@Author Felix Hedenström
args is a list containing arrays with sames sizes.
Example:
calling getTable([names, numberofgoals], ["Names", "Goals"])
where   names           = ["bob", "peter", "alex"]
and     numberofgoals   = [4, 5, 7]
will return a string that looks like
+-----+-----+
|Names|Goals|
+-----+-----+
|bob  |4    |
|peter|5    |
|alex |7    |
+-----+-----+
"""
def get_table(args, legend = []):
    colums = len(args)
    rows = len(args[0])

    for arg in args[1:]:
        assert len(arg) == rows, "Not same length on all args."

    if legend == []:
        useLegend = False
        longest = [0] * colums
    else:
        assert len(legend) == colums, "Length of legend not the same as number of data colums. len(legend) = {}, len(args) = {}".format(len(legend), len(args))
        useLegend = True
        longest = []
        for l in legend:
            longest.append(len(l))

    for i in range(len(args)):
        for w in args[i]:
            length = len(str(w)) + 1
            if length > longest[i]:
                longest[i] = length
    line = "+"
    for i in range(colums):
        line += "-" * longest[i]
        line += "+"
    line += "\n"
    ans = line
    if useLegend:
        ans += "|"
        for i in range(len(legend)):
            ans += "{:{width}}|".format(legend[i], width=longest[i])
        ans += "\n"
        ans += line
    for i in range(rows):
        ans += "|"
        for j in range(colums):
            ans += "{:{width}}|".format(args[j][i], width=longest[j])
        ans += "\n"
    ans += line
    return ans

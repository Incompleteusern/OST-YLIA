from abc import ABC, abstractmethod
from enum import Enum

from von import api
import re
import logging

class Output:
    def __init__(self, input_file):
        self.out: str = ""
        self.input_file: str = input_file

    def __iadd__(self, addition: any):
        if not isinstance(addition, str):
            logging.warning("Converting object into string")
            addition = str(addition)

        if len(self.out) > 0:
            self.nl()

        self.out += addition

        return self

    def nl(self):
        self.out += "\n"

    def write(self):
        with open(f"out-{self.input_file}", "w") as f:
            f.write(self.out)

class VonType(Enum):
    E = 2
    M = 3
    H = 5
    Z = 9
    J = 17
    K = 33
    L = 65

    X = -1
    I = -2

    def isWalkthrough(self) -> bool:
        return self == VonType.X

    def isExample(self) -> bool:
        return self == VonType.I

    def isPractice(self) -> bool:
        return not (self.isWalkthrough() or self.isExample())

    @staticmethod
    def fromString(s: str) -> "VonType":
        type_chart = {
            "E": VonType.E,
            "M": VonType.M,
            "H": VonType.H,
            "Z": VonType.Z,
            "X": VonType.X,
            "I": VonType.I,
        }

        if s not in type_chart:
            logging.error(f"Invalid Von Type String {s}")

        return type_chart[s]


class Problem(ABC):
    def __init__(self, type: VonType, required: bool, name: str | None) -> None:
        self.type = type
        self.required = required
        self.name = name

    @abstractmethod
    def toString(self) -> str:
        pass


class VonProblem(Problem):
    def __init__(
        self, type: VonType, required: bool, source: str, name: str | None
    ) -> None:
        self.source: str = source

        if not api.has(self.source):
            raise ValueError("Missing from VON!")
        
        self.problem = api.get(self.source, True)
        self.puid = api.inferPUID(self.source)

        if name == "*" or name is None or len(name) == 0:
            name = self.source
        elif name.startswith("["):
            name = name[1:-1]

        super().__init__(type, required, name)

    def toString(self) -> str:
        if self.type.isPractice():
            return self.practiceString()
        if self.type.isWalkthrough():
            return self.exampleString(True)
        if self.type.isExample():
            return self.exampleString(False)

    def practiceString(self) -> str:
        string = ""

        if self.required:
            env = "reqproblem"
        else:
            env = "problem"

        if (url := self.problem.url) is not None and url != "<++>":
            name = f"\href{{{url}}}{{{self.name}}}"
        else:
            name = self.name

        string += f"\\begin{{{env}}}[{name}, ${self.type.value}\clubsuit$]"

        string += "\n\t" + self.problem.bodies[0].replace("\n", "\n\t")

        string += f"\n\\end{{{env}}} \printpuid{{{self.puid}}}"

        if self.name == self.source:
            solution_prompt = f"\n\n%% Type your solution to \href{{https://otis.evanchen.cc/arch/{self.puid}/otis/}}{{{self.puid}}} here ..."
        else:
            solution_prompt = f"\n\n%% Type your solution to {self.name} (\href{{https://otis.evanchen.cc/arch/{self.puid}/otis/}}{{{self.puid}}}) here ..."

        string += solution_prompt

        string += "\n\n%% --------------------------------------------------"

        return string

    def exampleString(self, walkthrough) -> str:
        string = ""

        if (url := self.problem.url) is not None and url != "<++>":
            name = f"\href{{{url}}}{{{self.name}}}"
        else:
            name = self.name

        # example

        string += f"\\begin{{example}}[{name}]"

        string += "\n\t" + self.problem.bodies[0].replace("\n", "\n\t")

        string += f"\n\\end{{example}} \printpuid{{{self.puid}}}"

        if walkthrough:
            string += "\n\n\\begin{walkthrough}"

            string += "\n\t" + self.problem.bodies[2].replace("\n", "\n\t")

            string += "\n\\end{walkthrough}"

            if self.name == self.source:
                solution_prompt = f"\n\n%% Type your response to \href{{https://otis.evanchen.cc/arch/{self.puid}/otis/}}{{{self.puid}}} here ..."
            else:
                solution_prompt = f"\n\n%% Type your response to {self.name} (\href{{https://otis.evanchen.cc/arch/{self.puid}/otis/}}{{{self.puid}}}) here ..."

            string += solution_prompt

            string += "\n\n%% --------------------------------------------------"

        return string


class CustomProblem(Problem):
    def __init__(
        self, type: VonType, required: bool, name: str | None, bodies: list[list[str]]
    ) -> None:
        if name.startswith("["):
            name = name[1:-1]

        super().__init__(type, required, name)

        self.bodies = bodies

    def toString(self) -> str:
        if self.type.isPractice():
            return self.practiceString()
        if self.type.isWalkthrough():
            return self.exampleString(True)
        if self.type.isExample():
            return self.exampleString(False)

    def practiceString(self) -> str:
        string = ""

        if self.required:
            env = "reqproblem"
        else:
            env = "problem"

        if self.name is not None and len(self.name) > 0:
            string += f"\\begin{{{env}}}[{self.name}, ${self.type.value}\clubsuit$]"
        else:
            string += f"\\begin{{{env}}}[${self.type.value}\clubsuit$]"

        string += "\n" + self.bodies[0]

        string += f"\\end{{{env}}}"

        if self.name is not None and len(self.name) > 0:
            solution_prompt = f"\n\n%% Type your solution to {self.name} here ..."
        else:
            solution_prompt = f"\n\n%% Type your solution here ..."

        string += solution_prompt

        string += "\n\n%% --------------------------------------------------"

        return string

    def exampleString(self, walkthrough) -> str:
        string = ""

        # example
        if self.name is not None and len(self.name) > 0:
            string += f"\\begin{{example}}[{self.name}]"
        else:
            string += f"\\begin{{example}}"

        string += "\n" + self.bodies[0]

        string += f"\\end{{example}}"

        if walkthrough:
            string += "\n\n\\begin{walkthrough}"

            string += "\n" + self.bodies[1]

            string += "\\end{walkthrough}"

            if self.name is not None and len(self.name) > 0:
                solution_prompt = f"\n\n%% Type your response to {self.name} here ..."
            else:
                solution_prompt = f"\n\n%% Type your response here ..."

            string += solution_prompt

            string += "\n\n%% --------------------------------------------------"

        return string


class Parser:
    def __init__(self, input_file):
        self.input_file: str = input_file

        self.goals: tuple[int]
        self.epigraph: str = ""
        self.problems: list[Problem] = []

    def parse(self):
        parsers: list[SubParser] = [
            VonSubParser(self),
            GoalSubParser(self),
            EpigraphSubParser(self),
            ProbCustomSubParser(self),
            ProbXICustomSubParser(self),
        ]

        active_parser: SubParser | None = None

        with open(self.input_file) as f:
            for _, line in enumerate(f):
                if active_parser is not None:
                    active_parser.continueParse(line)

                    if not active_parser.active():
                        active_parser = None
                    else:
                        continue

                for parser in parsers:
                    if parser.tryParse(line) and parser.active():
                        active_parser = parser
                        continue

class SubParser(ABC):
    def __init__(self, parent: Parser):
        self.parent = parent

    @abstractmethod
    def tryParse(self, line: str) -> bool:
        pass

    @abstractmethod
    def active(self) -> bool:
        pass

    @abstractmethod
    def continueParse(self, line: str):
        pass


class SingleParser(SubParser):
    @abstractmethod
    def parse(self, line: str):
        pass

    def tryParse(self, line: str) -> bool:
        self.parse(line)
        return False

    def active(self) -> bool:
        raise NotImplementedError

    def continueParse(self, line: str):
        raise NotImplementedError


VON_RE = re.compile(r"^\\von([EMHZXI])(R?)(\[.*?\]|\*)?\{(.*?)\}")


class VonSubParser(SingleParser):
    def parse(self, line: str):
        if (m := VON_RE.match(line)) is not None:
            type, required, name, source = m.groups()

            required = len(required) > 0
            vtype = VonType.fromString(type)
            self.parent.problems.append(VonProblem(vtype, required, source, name))


GOAL_RE = re.compile(r"^\\goals\{([0-9]+)\}\{([0-9]+)\}")


class GoalSubParser(SingleParser):
    def parse(self, line: str):
        if (m := GOAL_RE.match(line)) is not None:
            a, b = m.groups()
            self.parent.goals = (int(a), int(b))


class EpigraphSubParser(SubParser):
    def __init__(self, parent: Parser):
        super().__init__(parent)
        self.is_active = False

    def tryParse(self, line: str) -> bool:
        if line.startswith("\epigraph"):
            self.is_active = True
            self.total = 0
            self.count = 0

            self.countParen(line)

            return True

        return False

    def countParen(self, line: str):
        toAdd: str = ""

        for c in line:
            toAdd += c

            if c == "{":
                self.count += 1
            elif c == "}":
                self.count -= 1

                if self.count == 0:
                    self.total += 1

                    if self.total == 2:
                        self.is_active = False
                        self.parent.epigraph += toAdd

                        return

        self.parent.epigraph += line

    def active(self) -> bool:
        return self.is_active

    def continueParse(self, line: str):
        self.countParen(line)


PROB_START_RE = re.compile(r"^\\begin\{prob([EMHZXI])(R?)\}(\[.*?\])?")
PROB_END_RE = re.compile(r"^\\end\{prob([EMHZXI])(R?)\}")


class ProbCustomSubParser(SubParser):
    def __init__(self, parent: Parser):
        self.parent = parent
        self.is_active = False

    def tryParse(self, line: str) -> bool:
        if (m := PROB_START_RE.match(line)) is not None:
            type, required, name = m.groups()

            self.required = len(required) > 0
            
            self.name = name
            self.vtype = VonType.fromString(type)
            self.body = ""

            self.is_active = True

            return True

        return False

    def active(self) -> bool:
        
        return self.is_active

    def continueParse(self, line: str):
        if (m := PROB_END_RE.match(line)) is not None:
            self.is_active = False

            type, required = m.groups()

            assert self.required == (len(required) > 0)
            assert self.vtype == VonType.fromString(type)

            self.parent.problems.append(
                CustomProblem(self.vtype, self.required, self.name, [self.body])
            )
        else:
            self.body += line


EXAMPLE_START_RE = re.compile(r"^\\begin\{example\}(\[.*?\])?")
EXAMPLE_END_RE = re.compile(r"^\\end\{example\}")
WALKTHROUGH_START_RE = re.compile(r"^\\begin\{walkthrough\}(\[.*?\])?")
WALKTHROUGH_END_RE = re.compile(r"^\\end\{walkthrough\}")


class ProbXICustomSubParser(SubParser):
    def __init__(self, parent: Parser):
        self.parent = parent
        self.state = 0

    def tryParse(self, line: str) -> bool:
        if (m := EXAMPLE_START_RE.match(line)) is not None:
            (name,) = m.groups()

            self.name = name
            self.examplebody = ""
            self.walkthroughbody = ""

            self.state = 1

            return True

        return False

    def active(self) -> bool:
        
        return self.state > 0

    # STATES
    # 0: Not active
    # 1: Reading example
    # 2: Reading till walkthrough start
    # 3: Reading walkthrough

    def continueParse(self, line: str):
        if self.state == 1:
            if (EXAMPLE_END_RE.match(line)) is not None:
                self.state = 2
                
            else:
                self.examplebody += line
        elif self.state == 2:
            if line.isspace():
                return
            elif WALKTHROUGH_START_RE.match(line):
                self.state = 3
                
            else:
                self.state = 0

                self.parent.problems.append(
                    CustomProblem(VonType.I, False, self.name, [self.examplebody])
                )
        elif self.state == 3:
            if (WALKTHROUGH_END_RE.match(line)) is not None:
                self.state = 0

                self.parent.problems.append(
                    CustomProblem(
                        VonType.X,
                        False,
                        self.name,
                        [self.examplebody, self.walkthroughbody],
                    )
                )
            else:
                self.walkthroughbody += line


class Writer:
    def __init__(self, input_file: str):
        self.input_file = input_file

    def write(self):
        parser = Parser(self.input_file)
        parser.parse()

        output = Output(self.input_file)

        with open("preamble.txt") as f:
            output += f.read()

        output += "\\begin{document}"

        output += f"\\title{{Submission for {self.input_file.rsplit('.', 1)[0]}}}"

        output += """
\\subtitle{OTIS (internal use)}
\\author{YOUR NAME HERE}
\\date{\\today}
\\maketitle
        """

        examples = []
        practice = []

        for problem in parser.problems:
            if problem.type.isPractice():
                practice.append(problem)
            else:
                examples.append(problem)

        output += "\\section{Examples}"

        for problem in examples:
            string = problem.toString()

            if string != "":
                output.nl()
                output += string

        output += "\n\\section{Problems}"
        output.nl()
        output += f"\goals{{{parser.goals[0]}}}{{{parser.goals[1]}}}"
        output.nl()

        output += parser.epigraph

        for problem in practice:
            string = problem.toString()

            if string != "":
                output.nl()
                output += string

        output.nl()

        output += "\end{document}"

        output.write()

    pass


w = Writer("DNY-not-ntconstruct.tex")
w.write()

def main():
    commands = load_history("unixhist.txt")
    model = Model()

    for command in commands:
        model.update(command)

    print(evaluate_model(model, commands))


def evaluate_model(model, commands):
    successes = 0
    failures = 0

    for i in range(len(commands)-1):
        next_command = commands[i+1]
        predicted_commands = model.predict(commands[i], 5)
        #print(next_command, predicted_commands)
        if next_command in predicted_commands:
            successes += 1
        else:
            failures += 1

    return successes/(successes+failures)


class Model:
    def __init__(self):
        self.command_to_index = {}
        self.index_to_command = {}
        self.c = []
        self.alpha = 0.8
        self.initial_value = 1
        self.previous_command = None

    def update(self, current_command):
        if current_command not in self.command_to_index:
            self.command_to_index[current_command] = len(self.command_to_index)
            self.index_to_command[len(self.command_to_index)-1] = current_command
            self.c.append([self.initial_value for _ in range(len(self.command_to_index))])

            if len(self.command_to_index) != 1:
                for i in range(len(self.command_to_index)-1):
                    self.c[i].append(min(self.c[i]))

        if self.previous_command is None:
            self.previous_command = current_command
            return

        previous_command_index = self.command_to_index[self.previous_command]
        current_command_index = self.command_to_index[current_command]

        for i in range(len(self.c[previous_command_index])):
            self.c[previous_command_index][i] = self.c[previous_command_index][i] * self.alpha

        self.c[previous_command_index][current_command_index] \
            = self.c[previous_command_index][current_command_index] + (1-self.alpha)

        self.previous_command = current_command

    def predict(self, current_command, n):
        row = self.c[self.command_to_index[current_command]]
        indices = [i for i in range(0, len(row))]
        values_dict = dict(zip(indices, row))
        sorted_dict = {k: v for k, v in sorted(values_dict.items(), key=lambda item: item[1], reverse=True)}

        result = []
        for i in range(n):
            predicted_index = list(sorted_dict.keys())[i]
            result.append(self.index_to_command.get(predicted_index))

        return result


def load_history(filename):
    commands = []
    with open(filename, 'r') as file:
        for line in file.readlines():
            if line[0].isalpha():
                commands.append(line.replace('\n', ''))
    return commands


if __name__ == "__main__":
    main()

import matplotlib.pyplot as plt
import collections


def main():
    commands = load_history("unixhist.txt")
    train_commands = commands[:round(len(commands) / 2)]
    eval_commands = commands[round(len(commands) / 2):]
    model = Model()

    for command in train_commands:
        model.update(command)

    print(f'All commands (dataset) {len(commands)}')
    different_commands = len(set(commands))
    print(f'Different commands {different_commands}')
    print(f'Final evaluation (prediction is in top 3): {evaluate_model(model, eval_commands, top_n=3)}')

    # most common commands:
    counter = collections.Counter(commands)
    print(f'Top 5 commands: {counter.most_common(5)}')
    counter_items = sorted(counter.items(), key=lambda i: i[1])
    plt.pie(
        [v for k, v in counter_items],
        labels=[k for k, v in counter_items]
    )
    plt.title('Commands in data')
    plt.show()

    # most common pairs
    commands_in_pairs = []
    for command, next_command in zip(commands, commands[1:]):
        commands_in_pairs.append(f'{command}; {next_command}')
    counter = collections.Counter(commands_in_pairs)
    print(f'Top 5 pairs: {counter.most_common(5)}')
    counter_items = sorted(counter.items(), key=lambda i: i[1])
    plt.pie(
        [v for k, v in counter_items],
        labels=[k for k, v in counter_items]
    )
    plt.title('Most common command pairs')
    plt.show()

    top = [1, 2, 3, 4, 5, 6, 7, 8]
    evaluations = [evaluate_model(model, eval_commands, top_n=t) for t in top]
    plt.plot(top, evaluations)
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title('Prediction success rate (all commands)')
    plt.show()

    # most often used commands
    counter = collections.Counter(commands)
    most_frequent_commands = set(k for k, v in counter.most_common()[:round(different_commands * 0.1)])
    print(
        f'Top 10% of all different commands ({len(most_frequent_commands)}/{different_commands}): {most_frequent_commands}')
    # take commands, that count for 50% of all data
    # most_frequent_commands = set()
    # usegaes = 0
    # for command, nr_of_usages in counter.most_common():
    #     if usegaes > len(commands) / 2:
    #         break
    #     usegaes += nr_of_usages
    #     most_frequent_commands.add(command)

    evaluations = [
        evaluate_model(model, eval_commands, top_n=t, predict_only_commands=most_frequent_commands)
        for t in top
    ]

    plt.plot(top, evaluations)
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title(f'Prediction success rate ({len(most_frequent_commands)} most frequent commands)')
    plt.show()

    # least often used commands
    counter = collections.Counter(commands)
    least_frequent_commands = set(k for k, v in counter.most_common()[:round(different_commands * 0.5):-1])
    print(
        f'Least 10% of all different commands ({len(least_frequent_commands)}/{different_commands}): {least_frequent_commands}')
    # take commands, that count for 10% of all data
    # usegaes = 0
    # for command, nr_of_usages in counter.most_common()[::-1]:
    #     if usegaes > len(commands) / 10:
    #         break
    #     usegaes += nr_of_usages
    #     least_frequent_commands.add(command)

    evaluations = [
        evaluate_model(model, eval_commands, top_n=t, predict_only_commands=least_frequent_commands)
        for t in top
    ]

    plt.plot(top, evaluations)
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title(f'Prediction success rate ({len(least_frequent_commands)} least frequent commands)')
    plt.show()


def evaluate_model(model, commands, top_n=3, predict_only_commands: set = None):
    successes = 0
    failures = 0
    predict_only_commands = predict_only_commands or set()

    for i in range(len(commands) - 1):
        next_command = commands[i + 1]
        predicted_commands = model.predict(commands[i], top_n)
        if predict_only_commands and commands[i] not in predict_only_commands:
            continue
        if next_command in predicted_commands:
            successes += 1
        else:
            failures += 1

    return successes / (successes + failures)


class Model:
    def __init__(self):
        self.command_to_index = {}
        self.index_to_command = {}
        self.c = []
        self.default_row = [1]
        self.alpha = 0.8
        self.initial_value = 1
        self.previous_command = None

    def update(self, current_command):
        if current_command not in self.command_to_index:
            self.command_to_index[current_command] = len(self.command_to_index)
            self.index_to_command[len(self.command_to_index) - 1] = current_command
            self.c.append([self.initial_value for _ in range(len(self.command_to_index))])

            if len(self.command_to_index) != 1:
                for i in range(len(self.command_to_index) - 1):
                    self.c[i].append(min(self.c[i]))

                self.default_row.append(min(self.default_row))

        if self.previous_command is None:
            self.previous_command = current_command
            return

        previous_command_index = self.command_to_index[self.previous_command]
        current_command_index = self.command_to_index[current_command]

        for i in range(len(self.c[previous_command_index])):
            self.c[previous_command_index][i] = self.c[previous_command_index][i] * self.alpha
            self.default_row[i] = self.default_row[i] * self.alpha

        self.c[previous_command_index][current_command_index] \
            = self.c[previous_command_index][current_command_index] + (1 - self.alpha)

        self.default_row[current_command_index] = self.default_row[current_command_index] + (1 - self.alpha)

        self.previous_command = current_command

    def predict(self, current_command, n):
        try:
            row = self.c[self.command_to_index[current_command]]
        except KeyError:
            row = self.default_row
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

import matplotlib.pyplot as plt
import collections
import numpy as np
import seaborn as sns


def main():
    commands = load_history("unixhist.txt")
    top = [1, 2, 3, 4, 5, 6, 7, 8]
    # model = Model(0.8)
    # train_commands = commands[:round(len(commands) / 2)]
    # eval_commands = commands[round(len(commands) / 2):]
    # for command in train_commands:
    #     model.update(command)
    # show_model(model, commands, eval_commands)
    # plot_heatmap(model)
    # evaluate_most_common_commands(commands)
    # find_most_common_pairs(commands)
    # find_most_ofter_used_commands(model, commands, eval_commands, top)
    # find_least_often_used_commands(model, commands, eval_commands, top)

    alphas = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    make_evaluations_for_alpha(alphas, top, commands)


def make_evaluations_for_alpha(alphas, top, commands):
    train_commands = commands[:round(len(commands) / 2)]
    eval_commands = commands[round(len(commands) / 2):]

    lines = []
    for alpha in alphas:
        model = Model(alpha)
        for command in train_commands:
            model.update(command)

        evaluations = [evaluate_model(model, eval_commands, top_n=t) for t in top]
        line, = plt.plot(top, evaluations, label="alpha = " + str(alpha))
        lines.append(line)
        print("Model has been evaluated for alpha: " + str(alpha))

    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title('Prediction success rate (all commands)')
    plt.legend(handles=lines)
    plt.show()


def find_least_often_used_commands(model, commands, eval_commands, top):
    counter = collections.Counter(commands)
    different_commands = len(set(commands))
    least_frequent_commands = set(k for k, v in counter.most_common()[:round(different_commands * 0.5):-1])
    print(f'Least 10% of all different commands ({len(least_frequent_commands)}/{different_commands}): {least_frequent_commands}')
    evaluations = [
        evaluate_model(model, eval_commands, top_n=t, predict_only_commands=least_frequent_commands)
        for t in top
    ]

    plt.plot(top, evaluations)
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title(f'Prediction success rate ({len(least_frequent_commands)} least frequent commands)')
    plt.show()


def find_most_ofter_used_commands(model, commands, eval_commands, top):
    counter = collections.Counter(commands)
    different_commands = len(set(commands))
    most_frequent_commands = set(k for k, v in counter.most_common()[:round(different_commands * 0.1)])
    print(f'Top 10% of all different commands ({len(most_frequent_commands)}/{different_commands}): {most_frequent_commands}')

    evaluations = [
        evaluate_model(model, eval_commands, top_n=t, predict_only_commands=most_frequent_commands)
        for t in top
    ]

    plt.plot(top, evaluations)
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.title(f'Prediction success rate ({len(most_frequent_commands)} most frequent commands)')
    plt.show()


def show_model(model, commands, eval_commands):
    print(f'All commands (dataset) {len(commands)}')
    different_commands = len(set(commands))
    print(f'Different commands {different_commands}')
    print(f'Final evaluation (prediction is in top 3): {evaluate_model(model, eval_commands, top_n=3)}')


def plot_heatmap(model):
    weights = np.array(model.c)
    ax = sns.heatmap(weights)
    plt.show()


def evaluate_most_common_commands(commands):
    counter = collections.Counter(commands)
    print(f'Top 5 commands: {counter.most_common(5)}')
    counter_items = sorted(counter.items(), key=lambda i: i[1])
    plt.pie(
        [v for k, v in counter_items],
        labels=[k for k, v in counter_items]
    )
    plt.title('Commands in data')
    plt.show()


def find_most_common_pairs(commands):
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
    def __init__(self, alpha):
        self.command_to_index = {}
        self.index_to_command = {}
        self.c = []
        self.default_row = [1]
        self.alpha = alpha
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

import collections
import matplotlib.pyplot as plt

from models import IOLA, MostUsed, Bigram, Trigram


def evaluate_model(model, commands, top_n=3, predict_only_commands: set = None):
    successes = 0
    failures = 0
    predict_only_commands = predict_only_commands or set()

    for i in range(len(commands) - 1):
        next_command = commands[i + 1]
        predicted_commands = model.predict(commands[i], top_n)
        # print(next_command, predicted_commands)
        if predict_only_commands and commands[i] not in predict_only_commands:
            continue
        if next_command in predicted_commands:
            successes += 1
        else:
            failures += 1

    return successes / (successes + failures)


def load_history(filename):
    commands = []
    with open(filename, 'r') as file:
        for line in file.readlines():
            if line[0].isalpha():
                commands.append(line.replace('\n', ''))
    return commands


if __name__ == "__main__":
    models = [IOLA(), MostUsed(), Bigram(), Trigram()]

    commands = load_history("unixhist.txt")
    train_commands = commands[:round(len(commands) / 2)]
    eval_commands = commands[round(len(commands) / 2):]

    for command in train_commands:
        for model in models:
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
    plt.savefig('charts/commands_in_data.png')
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
    plt.title(f'Most common command pairs')
    plt.savefig('charts/command_pairs_in_data.png')
    plt.show()

    top = [1, 2, 3, 4, 5, 6, 7, 8]
    # evaluations = [evaluate_model(model, eval_commands, top_n=t) for t in top]
    # plt.plot(top, evaluations)
    evals = {}
    for model in models:
        evals[model.name] = [
            evaluate_model(model, eval_commands, top_n=t)
            for t in top
        ]

    for model_name, evaluations in evals.items():
        plt.plot(top, evaluations, label=model_name)
    plt.legend()
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.yticks([i / 10 for i in range(11)])
    plt.title(f'Prediction success rate (all commands)')
    plt.savefig(f'charts/prediction_success_rate.png')
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

    evals = {}
    for model in models:
        evals[model.name] = [
            evaluate_model(model, eval_commands, top_n=t, predict_only_commands=most_frequent_commands)
            for t in top
        ]

    for model_name, evaluations in evals.items():
        plt.plot(top, evaluations, label=model_name)
    plt.legend()
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.yticks([i / 10 for i in range(11)])
    plt.title(f'Prediction success rate ({len(most_frequent_commands)} most frequent commands)')
    plt.savefig(f'charts/prediction_success_rate_most_freq.png')
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

    evals = {}
    for model in models:
        evals[model.name] = [
            evaluate_model(model, eval_commands, top_n=t, predict_only_commands=least_frequent_commands)
            for t in top
        ]

    for model_name, evaluations in evals.items():
        plt.plot(top, evaluations, label=model_name)
    plt.legend()
    plt.xlabel('Top n predictions')
    plt.ylabel('Success rate')
    plt.yticks([i / 10 for i in range(11)])
    plt.title(f'Prediction success rate ({len(least_frequent_commands)} least frequent commands)')
    plt.savefig(f'charts/prediction_success_rate_least_freq.png')
    plt.show()

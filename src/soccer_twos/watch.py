import argparse
import importlib
import inspect
import logging
import os
import sys

import soccer_twos
from soccer_twos.agent_interface import AgentInterface


def get_agent_class(module):
    for class_name, class_type in inspect.getmembers(module, inspect.isclass):
        if class_name != "AgentInterface" and issubclass(class_type, AgentInterface):
            logging.info(f"Found agent {class_name} in module {module.__name__}")
            return class_type

    raise ValueError(
        "No AgentInterface subclass found in module {}".format(module.__name__)
    )


if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=LOGLEVEL)

    parser = argparse.ArgumentParser(description="Rollout soccer-twos.")
    parser.add_argument("-m", "--agent-module", help="Selfplay Agent Module")
    parser.add_argument("-m1", "--agent1-module", help="Team 1 Agent Module")
    parser.add_argument("-m2", "--agent2-module", help="Team 2 Agent Module")
    args = parser.parse_args()

    if args.agent_module:
        agent1_module_name = args.agent_module
        agent2_module_name = args.agent_module
    elif args.agent1_module and args.agent2_module:
        agent1_module_name = args.agent1_module
        agent2_module_name = args.agent2_module
    else:
        parser.print_help(sys.stderr)
        raise ValueError("Must specify agent module")

    # import agent modules
    agent1_module = importlib.import_module(agent1_module_name)
    agent2_module = importlib.import_module(agent2_module_name)
    # instantiate env so agents can access e.g. env.action_space.shape
    env = soccer_twos.make()
    agent1 = get_agent_class(agent1_module)(env)
    agent2 = get_agent_class(agent2_module)(env)
    env.close()
    # setup & run
    env = soccer_twos.make(watch=True)
    obs = env.reset()
    team0_reward = 0
    team1_reward = 0
    while True:
        # use agent1 as controller for team 0 and vice versa
        agent1_actions = agent1.act({0: obs[0], 1: obs[1]})
        agent2_actions = agent2.act({0: obs[2], 1: obs[3]})
        actions = {
            0: agent1_actions[0],
            1: agent1_actions[1],
            2: agent2_actions[0],
            3: agent2_actions[1],
        }

        # step
        obs, reward, done, info = env.step(actions)

        # logging
        team0_reward += reward[0] + reward[1]
        team1_reward += reward[2] + reward[3]
        if max(done.values()):  # if any agent is done
            logging.info(f"Total Reward: {team0_reward} x {team1_reward}")
            team0_reward = 0
            team1_reward = 0
            env.reset()

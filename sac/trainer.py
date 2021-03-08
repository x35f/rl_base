from common.trainer import BaseTrainer
import numpy as np
from tqdm import tqdm
from time import time
class SACTrainer(BaseTrainer):
    def __init__(self, agent, env, buffer, logger, **kwargs):
        self.agent = agent
        self.buffer = buffer
        self.logger = logger
        self.env = env 
        #hyperparameters
        self.batch_size = kwargs['batch_size']
        self.num_updates_per_ite = kwargs['num_updates_per_ite']
        self.max_traj_length = kwargs['max_traj_length']
        self.test_interval = kwargs['test_interval']
        self.trajs_per_test = kwargs['trajs_per_test']


    def train(self, max_episode):
        tot_num_updates = 0
        train_traj_rewards = []
        episode_durations = []

        for episode in range(max_episode):
            episode_start_time = time()
            #rollout in environment and add to buffer
            state = self.env.reset()
            done = False
            traj_reward = 0
            traj_length = 0
            for i in tqdm(range(self.max_traj_length)):
                action = self.agent.select_action(state)
                next_state, reward, done, _ = self.env.step(action)
                traj_length  += 1
                traj_reward += reward
                self.buffer.add_tuple(state, action, next_state, reward, float(done))
                state = next_state
                if done:
                    break
            train_traj_rewards.append(traj_reward)
            self.logger.log_var("return/train",traj_reward,tot_num_updates)
            #update network
            for update in range(self.num_updates_per_ite):
                data_batch = self.buffer.sample_batch(self.batch_size)
                critic_loss1, critic_loss2, policy_loss, entropy_loss, alpha = agent.update(data_batch)
                self.logger.log_var("loss/critic1",critic_loss1,tot_num_updates)
                self.logger.log_var("loss/critic2",critic_loss2,tot_num_updates)
                self.logger.log_var("loss/policy",policy_loss,tot_num_updates)
                self.logger.log_var("loss/entropy",entropy_loss,tot_num_updates)
                self.logger.log_var("others/entropy_alpha",alpha,tot_num_updates)
                tot_num_updates += 1

            if tot_num_updates % self.test_interval == 0:
                avg_test_reward = self.test()
                self.logger.log_var("return/test", avg_test_reward, tot_num_updates)
            episode_end_time = time()
            episode_duration = episode_end_time - episode_start_time
            episode_durations.append(episode_duration)
            print("episode {}: return {} eta: {}s".format(episode, np.mean(train_traj_rewards[-2:], int(np.mean(episode_durations[-5:])))))



    def test(self):
        rewards = []
        for i in range(self.trajs_per_test):
            traj_reward = 0
            state = self.env.reset()
            for i in range(self.max_traj_length):
                action = self.agent.select_action(state, evaluate=True)
                next_state, reward, done, _ = self.env.step(action)
                traj_reward += reward
                state = next_state
                if done:
                    break
            rewards.append(traj_reward)
        return np.mean(rewards)
            


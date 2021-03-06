import caffe
import numpy as np

class SoftmaxSoftLabel(caffe.Layer):
    """
    Compute the Softmax Loss in the same manner but consider soft labels
    as the ground truth
    """
    def setup(self, bottom, top):
        # check input pair
        if len(bottom) != 3:
            raise Exception("Need three inputs to compute distance (infered,labels and reliability).")

    def reshape(self, bottom, top):
        # check input dimensions match
        if bottom[0].num != bottom[1].num:
            raise Exception("Infered scores and labels must have the same dimension.")
        if bottom[0].num != bottom[2].num:
            raise Exception("Reliability scores wrong dimension.")
        # difference is shape of inputs
        self.diff = np.zeros_like(bottom[0].data, dtype=np.float32)
        # loss output is scalar
        top[0].reshape(1)


    def forward(self, bottom, top):
        labels_scores = bottom[2].data
        labels = bottom[1].data
        scores = bottom[0].data

        #normalizing to avoid instability
        scores -= np.max(scores, axis=1, keepdims=True)
        exp_scores = np.exp(scores)
        probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)

        correct_logprobs = np.zeros([bottom[0].num,1])
        for r in range(bottom[0].num):
            correct_logprobs[r] = -np.log(probs[r,int(labels[r])]) * labels_scores[r]

        data_loss = np.sum(correct_logprobs) / bottom[0].num

        self.diff[...] = probs
        top[0].data[...] = data_loss


    def backward(self, top, propagate_down, bottom):
        delta = self.diff
        scores = bottom[0].data
        labels = bottom[1].data
        labels_scores = bottom[2].data

        for i in range(2):
            if not propagate_down[i]:
                continue
            if i == 0:
                for r in range(bottom[0].num):
                    delta[r, int(labels[r])] -= 1
                    delta[r,:] *= labels_scores[r]


                bottom[i].diff[...] = delta / bottom[0].num

                # # Numerical gradient
                # epsilon = 1e-6
                # scores -= np.max(scores)
                #
                # # GradPlus
                # scoresPlus = scores + epsilon
                # scoresPlus = np.exp(scoresPlus)
                # probsPlus = scoresPlus / np.sum(scoresPlus, axis=1, keepdims=True)
                # correct_logprobsPlus = np.zeros([bottom[0].num, 1])
                # for r in range(bottom[0].num):
                #     correct_logprobsPlus[r] = -np.log(probsPlus[r, int(labels[r])]) * labels_scores[r]
                # gradPlus = np.sum(correct_logprobsPlus) / bottom[0].num
                #
                # # GradMinus
                # scoresMinus = scores - epsilon
                # scoresMinus = np.exp(scoresMinus)
                # probsMinus = scoresMinus / np.sum(scoresMinus, axis=1, keepdims=True)
                # correct_logprobsMinus = np.zeros([bottom[0].num, 1])
                # for r in range(bottom[0].num):
                #     correct_logprobsMinus[r] = -np.log(probsMinus[r, int(labels[r])]) * labels_scores[r]
                # gradMinus = np.sum(correct_logprobsMinus) / bottom[0].num
                #
                # grad = (gradPlus - gradMinus) / (2. * epsilon)
                #
                # print "Numerical gradient: " + str(grad)
                # print "Backprop gradient: " + str(np.sum(bottom[0].diff))
                # print('\n')



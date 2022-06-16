from ctypes import ArgumentError
from pathlib import Path

import torch
from model.dataset import Vocab
from model.pluginVAE import PluginVAE
from utils import eval
import json

from easydict import EasyDict
from model.pretrainVAE import PretrainVAE

def get_args(inputs):
    args = {
        'device': 'cpu',
        'token': {
            'pad_token': 0,
            'oov_token': 1,
            'start_token': 2,
            'end_token': 3
        },
        'max_len': 17,
        'vocab_path': 'vocab/poem.json',
        'pretrain': {
            'path': 'checkpoint/v0_0_1_best.pkl',
            'latent_dim': 128
        },
        'input': inputs
    }
    return EasyDict(args)

def generate(args):
    # Get input data
    if hasattr(args, 'input'):
        input_sentence = args.input
    else:
        input_sentence = None

    # Load vocab
    vocab = Vocab.load(args.vocab_path, args.token)

    # Setup model
    if not hasattr(args, 'pretrain'):
        raise ArgumentError('PretrainVAE are MUST loaded to generate.')
    pretrain = PretrainVAE(max_vocab=len(vocab)).to(args.device)
    pretrain_ckp = torch.load(args.pretrain.path, map_location=args.device)
    pretrain.load_state_dict(pretrain_ckp['model'])
    pretrain.eval()

    if not hasattr(args, 'plugin'):
        args.plugin = None
    if args.plugin is not None:
        plugin = PluginVAE().to(args.device)
        plugin_ckp = torch.load(args.plugin.path, map_location=args.device)
        plugin.load_state_dict(plugin_ckp['model'])
        plugin.eval()
    else:
        plugin = None
    # Turn on model eval

    # Generation
    if input_sentence is not None:
        output_sentence = eval.gen_from_sentence(
            input_sentence, vocab, pretrain, None
        )
        output_sentence = output_sentence[1:-1]
        return ' '.join(output_sentence)
    else:
        gen_num = 1
        gen = eval.gen_from_ae(
            1.0, gen_num, vocab, pretrain, plugin,
            latent_dim=args.pretrain.latent_dim,
            max_len=args.max_len,
            argmax_flag=True,
            device=args.device
        )
        r = []
        for g in gen[0]:
            g = g[1:-1]
            r.append(' '.join([vocab.id2char[str(idx)] for idx in g]))
        return r

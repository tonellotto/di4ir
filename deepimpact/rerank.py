import os
import random

from argparse import ArgumentParser
from deepimpact.parameters import DEFAULT_DATA_DIR, DEVICE
from deepimpact.utils import print_message, create_directory

from deepimpact.evaluation.loaders import load_colbert, load_topK, load_qrels
from deepimpact.indexing.loaders import load_document_encodings

from deepimpact.evaluation.ranking import evaluate
from deepimpact.evaluation.metrics import evaluate_recall


def main():
    random.seed(123456)

    parser = ArgumentParser(description='Exhaustive (non-index-based) evaluation of re-ranking with ColBERT.')

    parser.add_argument('--checkpoint', dest='checkpoint', required=True)
    parser.add_argument('--topk', dest='topK', required=True)
    parser.add_argument('--qrels', dest='qrels', default=None)

    parser.add_argument('--index', dest='index', required=True)
    parser.add_argument('--index_dir', dest='index_dir', default='outputs.index/')

    parser.add_argument('--data_dir', dest='data_dir', default=DEFAULT_DATA_DIR)
    parser.add_argument('--output_dir', dest='output_dir', default='outputs.rerank/')

    parser.add_argument('--bsize', dest='bsize', default=128, type=int)
    parser.add_argument('--subsample', dest='subsample', default=None)  # TODO: Add this

    # TODO: For the following four arguments, default should be None. If None, they should be loaded from checkpoint.
    parser.add_argument('--similarity', dest='similarity', default='cosine', choices=['cosine', 'l2'])
    parser.add_argument('--dim', dest='dim', default=128, type=int)
    parser.add_argument('--query_maxlen', dest='query_maxlen', default=32, type=int)
    parser.add_argument('--doc_maxlen', dest='doc_maxlen', default=180, type=int)

    args = parser.parse_args()
    args.input_arguments = args
    args.run_name = args.topK
    args.shortcircuit = False

    create_directory(args.output_dir)

    args.topK = os.path.join(args.data_dir, args.topK)

    if args.qrels:
        args.qrels = os.path.join(args.data_dir, args.qrels)

    args.colbert, args.checkpoint = load_colbert(args)
    args.qrels = load_qrels(args.qrels)
    args.queries, args.topK_docs, args.topK_pids = load_topK(args.topK)

    evaluate_recall(args.qrels, args.queries, args.topK_pids)

    args.index = os.path.join(args.index_dir, args.index)
    args.index = load_document_encodings(args.index)
    evaluate(args, args.index)


if __name__ == "__main__":
    main()

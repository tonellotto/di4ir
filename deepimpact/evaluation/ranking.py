import os
import random
import time
import torch

from deepimpact.utils import print_message, load_checkpoint, batch
from deepimpact.evaluation.metrics import Metrics


def rerank(args, query, pids, passages, index=None):
    colbert = args.colbert
    #tokenized_passages = list(args.pool.map(colbert.tokenizer.tokenize, passages))
    scores = [colbert.forward([query] * len(D), D)[0].cpu() for D in batch(passages, args.bsize)]
    scores = torch.cat(scores).squeeze(1).sort(descending=True)
    ranked = scores.indices.tolist()
    ranked_scores = scores.values.tolist()
    ranked_pids = [pids[position] for position in ranked]
    ranked_passages = [passages[position] for position in ranked]

    assert len(ranked_pids) == len(set(ranked_pids))

    return list(zip(ranked_scores, ranked_pids, ranked_passages))


def evaluate(args, index=None):
    qrels, queries, topK_docs, topK_pids = args.qrels, args.queries, args.topK_docs, args.topK_pids

    metrics = Metrics(mrr_depths={10}, recall_depths={50, 200, 1000}, total_queries=None)

    if index:
        args.buffer = torch.zeros(1000, args.doc_maxlen, args.dim, dtype=index[0].dtype)

    output_path = '.'.join([str(x) for x in [args.run_name, 'tsv', int(time.time())]])
    output_path = os.path.join(args.output_dir, output_path)

    # TODO: Save an associated metadata file with the args.input_args

    with open(output_path, 'w') as outputfile:
        with torch.no_grad():
            keys = sorted(list(queries.keys()))
            random.shuffle(keys)

            for query_idx, qid in enumerate(keys):
                query = queries[qid]
                print_message(query_idx, qid, query, '\n')

                if qrels and args.shortcircuit and len(set.intersection(set(qrels[qid]), set(topK_pids[qid]))) == 0:
                    continue

                ranking = rerank(args, query, topK_pids[qid], topK_docs[qid], index)

                for i, (score, pid, passage) in enumerate(ranking):
                    outputfile.write('\t'.join([str(x) for x in [qid, pid, i+1]]) + "\n")

                    if i+1 in [1, 2, 5, 10, 20, 100]:
                        print("#> " + str(i+1) + ") ", pid, ":", score, '    ', passage)

                if qrels:
                    metrics.add(query_idx, qid, ranking, qrels[qid])

                    for i, (score, pid, passage) in enumerate(ranking):
                        if pid in qrels[qid]:
                            print("\n#> Found", pid, "at position", i+1, "with score", score)
                            print(passage)

                    metrics.print_metrics(query_idx)

                print_message("#> checkpoint['batch'] =", args.checkpoint['batch'], '\n')
                print("output_path =", output_path)
                print("\n\n")

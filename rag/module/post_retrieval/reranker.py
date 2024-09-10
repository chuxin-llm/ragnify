
from typing import List, Dict, Tuple, Type, Union
from tqdm import tqdm
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForCausalLM
)

from langchain_core.documents import Document
from rag.common.configuration import settings


class Reranker:

    """
    support to use rerank models like:
    1. FlagEmbedding: https://github.com/FlagOpen/FlagEmbedding
    2. BCEEmbedding: https://github.com/netease-youdao/BCEmbedding
    3. https://github.com/UKPLab/sentence-transformers/blob/737353354fbdf1a419eee864f998ffe9fdf3b682/sentence_transformers/cross_encoder/CrossEncoder.py#L20
    """

    def __init__(
            self,
            model_name_or_path: str = None,
            use_fp16: bool = False
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path)

        self.need_activate = True if "bce" in model_name_or_path.lower() else False

        pointed_device = settings.reranker.device
        if torch.cuda.is_available() and "cuda" in pointed_device:
            self.device = torch.device(pointed_device)
        else:
            self.device = torch.device('cpu')
            use_fp16 = False
        if use_fp16:
            self.model.half()

        self.model = self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def compute_score(self,
                      sentence_pairs: Union[List[Tuple[str, str]], Tuple[str, str]],
                      batch_size: int = 256,
                      max_length: int = 512,
                      enable_tqdm: bool=False,) -> List[float]:

        assert isinstance(sentence_pairs, list)
        if isinstance(sentence_pairs[0], str):
            sentence_pairs = [sentence_pairs]

        all_scores = []
        for start_index in tqdm(range(0, len(sentence_pairs), batch_size), desc="Compute Scores", disable=not enable_tqdm):
            sentences_batch = sentence_pairs[start_index:start_index + batch_size]
            inputs = self.tokenizer(
                sentences_batch,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=max_length,
            ).to(self.device)

            scores = self.model(**inputs, return_dict=True).logits.view(-1, ).float()
            if self.need_activate:
                scores = torch.sigmoid(scores)
            all_scores.extend(scores.cpu().numpy().tolist())

        # if len(all_scores) == 1:
        #     return all_scores[0]
        return all_scores

    def rank(self,
             query: str,
             docs: List[Document],
             top_k: int = None,
             batch_size: int = 16,
             return_documents: bool = True,):
        query_doc_pairs = [(query, doc.page_content) for doc in docs]
        scores = self.compute_score(
            query_doc_pairs,
            batch_size=batch_size
        )
        results = []
        for i in range(len(scores)):
            if return_documents:
                results.append({"corpus_id": i, "score": scores[i], "document": docs[i]})
            else:
                results.append({"corpus_id": i, "score": scores[i]})

        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class LLMReranker:
    def __init__(
            self,
            model_name_or_path: str = None,
            use_fp16: bool = False
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_name_or_path)

        self.yes_loc = self.tokenizer('Yes', add_special_tokens=False)['input_ids'][0]

        pointed_device = settings.reranker.device
        if torch.cuda.is_available() and "cuda" in pointed_device:
            self.device = torch.device(pointed_device)
        else:
            self.device = torch.device('cpu')
            use_fp16 = False
        if use_fp16:
            self.model.half()

        self.model = self.model.to(self.device)
        self.model.eval()

    def _get_inputs(self, pairs, tokenizer, prompt=None, max_length=1024):
        if prompt is None:
            prompt = "Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'."
        sep = "\n"
        prompt_inputs = tokenizer(prompt,
                                  return_tensors=None,
                                  add_special_tokens=False)['input_ids']
        sep_inputs = tokenizer(sep,
                               return_tensors=None,
                               add_special_tokens=False)['input_ids']
        inputs = []
        for query, passage in pairs:
            query_inputs = tokenizer(f'A: {query}',
                                     return_tensors=None,
                                     add_special_tokens=False,
                                     max_length=max_length * 3 // 4,
                                     truncation=True)
            passage_inputs = tokenizer(f'B: {passage}',
                                       return_tensors=None,
                                       add_special_tokens=False,
                                       max_length=max_length,
                                       truncation=True)
            item = tokenizer.prepare_for_model(
                [tokenizer.bos_token_id] + query_inputs['input_ids'],
                sep_inputs + passage_inputs['input_ids'],
                truncation='only_second',
                max_length=max_length,
                padding=False,
                return_attention_mask=False,
                return_token_type_ids=False,
                add_special_tokens=False
            )
            item['input_ids'] = item['input_ids'] + sep_inputs + prompt_inputs
            item['attention_mask'] = [1] * len(item['input_ids'])
            inputs.append(item)
        return tokenizer.pad(
                    inputs,
                    padding=True,
                    max_length=max_length + len(sep_inputs) + len(prompt_inputs),
                    pad_to_multiple_of=8,
                    return_tensors='pt',
                ).to(self.device)

    @torch.no_grad()
    def compute_score(self,
                      sentence_pairs: Union[List[Tuple[str, str]], Tuple[str, str]],
                      batch_size: int = 256,
                      max_length: int = 512,
                      enable_tqdm: bool=False,):
        all_scores = []
        for start_index in tqdm(range(0, len(sentence_pairs), batch_size), desc="Compute Scores",
                                disable=not enable_tqdm):
            sentences_batch = sentence_pairs[start_index:start_index + batch_size]

            inputs = self._get_inputs(sentences_batch, self.tokenizer)
            scores = self.model(**inputs, return_dict=True).logits[:, -1, self.yes_loc].view(-1, ).float()

            all_scores.extend(scores.cpu().numpy().tolist())

        if len(all_scores) == 1:
            return all_scores[0]
        return all_scores

    def rank(self,
             query: str,
             docs: List[Document],
             top_k: int = None,
             batch_size: int = 16,
             return_documents: bool = True,):
        query_doc_pairs = [(query, doc.page_content) for doc in docs]
        scores = self.compute_score(
            query_doc_pairs,
            batch_size=batch_size
        )
        results = []
        for i in range(len(scores)):
            if return_documents:
                results.append({"corpus_id": i, "score": scores[i], "document": docs[i]})
            else:
                results.append({"corpus_id": i, "score": scores[i]})

        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]
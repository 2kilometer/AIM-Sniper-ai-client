import os
import asyncio
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from polyglot_score.service.polyglot_score_service import PolyglotScoreService
from polyglot_score.repository.polyglot_score_repository_impl import PolyglotScoreRepositoryImpl
from template.utility.color_print import ColorPrinter


class PolyglotScoreServiceImpl(PolyglotScoreService):
    __instance = None
    # load lora adaptor merged model
    cacheDir = os.path.join("models", "cache")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


    config = {
        "pretrained_model_name_or_path": "EleutherAI/polyglot-ko-1.3b",
        "trust_remote_code": True,
        "local_files_only": True,
        "padding_side": "left",
        "max_token_length": 1024,
    }
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__polyglotScoreRepository = PolyglotScoreRepositoryImpl.getInstance()

            return cls.__instance

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()

        return cls.__instance

    async def scoreUserAnswer(self, *arg, **kwargs):
        cacheDir = os.path.join("models", "cache")
        if not os.path.exists(cacheDir):
            self.__polyglotScoreRepository.downloadPretrainedModel()

        interviewList = arg
        model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=self.config['pretrained_model_name_or_path'],
            trust_remote_code=self.config['trust_remote_code'],
            cache_dir=self.cacheDir,
            local_files_only=self.config['local_files_only'])

        tokenizer = (AutoTokenizer.
                     from_pretrained(pretrained_model_name_or_path=self.config['pretrained_model_name_or_path'],
                                     trust_remote_code=self.config['trust_remote_code'],
                                     cache_dir=self.cacheDir,
                                     local_files_only=self.config['local_files_only'],
                                     padding_side=self.config['padding_side']))

        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
        tokenizer.model_max_length = self.config['max_token_length']

        q1, q2, q3, q4, q5 = (interviewList[0], interviewList[1], interviewList[2],
                              interviewList[3], interviewList[4])
        # 각 인터뷰에 대해 비동기 작업 생성
        result1 = self.__polyglotScoreRepository.scoreUserAnswer(q1[0], q1[1], q1[2], model, tokenizer)
        result2 = self.__polyglotScoreRepository.scoreUserAnswer(q2[0], q2[1], q2[2], model, tokenizer)
        result3 = self.__polyglotScoreRepository.scoreUserAnswer(q3[0], q3[1], q3[2], model, tokenizer)
        result4 = self.__polyglotScoreRepository.scoreUserAnswer(q4[0], q4[1], q4[2], model, tokenizer)
        result5 = self.__polyglotScoreRepository.scoreUserAnswer(q5[0], q5[1], q5[2], model, tokenizer)
        # 모든 비동기 작업을 병렬로 실행
        resultList = [result1, result2, result3, result4, result5]
        ColorPrinter.print_important_message(f'resultList: {resultList}')
        return {'resultList': resultList}
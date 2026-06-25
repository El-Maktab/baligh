import time
from src.services.nws.features.nwp.word_ngram.serializer import load_ngram_model
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
from src.services.nws.features.nwp.lstm.model import LSTMNWPModel
from src.services.nws.features.nwp.hybrid.model import HybridArabicPredictor

def test():
    print("Loading N-Gram Model...")
    t0 = time.time()
    ngram_data = load_ngram_model("src/services/nws/data/word_ngram_lm_kaggle.msgpack.gz")
    ngram_model = WordNGramLM(ngram_data)
    print(f"Loaded in {time.time() - t0:.2f}s")
    
    print("Loading LSTM Model...")
    t0 = time.time()
    lstm_model = LSTMNWPModel(
        model_path="src/services/nws/data/best_model.pt",
        sp_model_path="src/services/nws/data/arabic_bpe.model"
    )
    print(f"Loaded in {time.time() - t0:.2f}s")
    
    hybrid = HybridArabicPredictor(neural_model=lstm_model, kn_model=ngram_model)
    
    tests = [
        "ذهبت إلى المدرسة",
        "الولايات المتحدة",
        "أحب أن أقرأ",
        "شرب الكلب الم"
    ]
    
    for t in tests:
        print(f"\nContext: {t}")
        results = hybrid.predict(t, top_k=5)
        for i, (word, score) in enumerate(results):
            print(f"  {i+1}. {word} (score: {score:.3f})")

if __name__ == "__main__":
    test()

@echo off
chcp 65001 >nul
echo ========================================
echo Installing Hebrew NLP Dependencies
echo for Keyword Density Analysis Module
echo ========================================
echo.

echo [1/4] Installing PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo [2/4] Installing Trankit (Hebrew morphology)...
pip install trankit

echo.
echo [3/4] Installing Transformers for DictaBERT...
pip install transformers

echo.
echo [4/4] Downloading Hebrew models (this may take a while)...
python -c "print('Loading Trankit Hebrew model...'); from trankit import Pipeline; p = Pipeline('hebrew'); print('Trankit ready!')"
python -c "print('Loading DictaBERT model...'); from transformers import AutoTokenizer, AutoModel; t = AutoTokenizer.from_pretrained('dicta-il/dictabert'); m = AutoModel.from_pretrained('dicta-il/dictabert'); print('DictaBERT ready!')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now use the advanced keyword density analyzer
echo with Hebrew morphology and semantic analysis.
echo.
pause


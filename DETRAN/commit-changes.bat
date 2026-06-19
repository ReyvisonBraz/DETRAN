@echo off
cd /d "%~dp0"
echo Fazendo commit das alteracoes...
git add frontend/app/globals.css
git add frontend/lib/auth.tsx
git add "frontend/app/(auth)/completar/page.tsx"
git add frontend/components/Onboarding.tsx
git add "frontend/app/(app)/dashboard/page.tsx"
git add "frontend/app/(app)/creditos/page.tsx"
git add "frontend/app/(app)/historico/page.tsx"
git add "frontend/app/(app)/consultas/page.tsx"
git add "frontend/app/(app)/perfil/page.tsx"
git add "frontend/app/resultado/[jobId]/page.tsx"
git add frontend/components/FeedbackWidget.tsx
git add frontend/components/Toast.tsx
git add firestore.rules
git add firestore.indexes.json
git add firebase.json
git add backend/app/firebase_storage.py
git add backend/app/runner.py
git add backend/requirements.txt
git add backend/.env.example
git status
git commit -m "feat: login Google, creditos, onboarding, historico, feedback, estorno automatico, perfil, toast, firestore rules, firebase storage PDFs"
git push origin main
echo.
echo Pronto! Vercel vai fazer o deploy automaticamente.
echo Lembre de configurar as variaveis do Firebase no Render (ver backend/.env.example).
pause

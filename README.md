# AZ-900 Local Question Set App

This is an offline Python/Tkinter practice-test application. Private question data is stored locally and is not included in the repository.

## Run

Double-click `run_app.bat`, or run:

```powershell
python az900_quiz_app.py
```

## Features

- Click an option, then click `Check`.
- Correct answers are highlighted green.
- Incorrect selected answers are highlighted red.
- Results show an estimated score on Microsoft's 1-1000 scale; the passing score is 700.
- Wrong answers are saved in `progress.json`.
- Use `Wrong Set` to practice only questions currently saved as wrong.
- If you answer a saved wrong question correctly, it is removed from the wrong set.
- Use the `Question Set` dropdown to switch between labeled mock tests.
- Use `Question List` to search by question number or text, then double-click a question to jump to it.
- Use the small `Lock` checkbox beside `Shuffle` to prevent accidental reshuffling; clear it to unlock Shuffle.
- Use `Start Exam (45 min)` for a timed exam with 45 random questions drawn across all available question sets.
- Exam answers are saved while you navigate, correctness stays hidden until submission, and incorrect or unanswered questions are added to their source question set's wrong list.

Microsoft uses scaled scoring, so an official score of 700 does not necessarily mean 70% of questions were answered correctly. This app uses equal question weights to provide a clearly labeled practice estimate; in a 45-question exam, that estimate requires at least 32 correct answers to reach 700.

## Files

- `az900_quiz_app.py`: GUI app.
- `run_app.bat`: Windows launcher.
- `.gitignore`: excludes private question content, progress, caches, and local files.
- `question_sets/`: local question data; ignored by Git.
- `question_assets/`: local question images; ignored by Git.
- `progress.json`: local progress data; ignored by Git.

If no local question set exists, the app creates a small example set automatically so the public code can still be started and tested.

## Privacy

Question sets, question images, imported source files, PDFs, and personal progress stay on the local machine. Do not force-add these ignored files to a public repository unless you have permission to distribute them.

## Add Another Mock Test

Create another local JSON file in `question_sets`, for example `my_test.json`:

```json
{
  "label": "My Test",
  "questions": [
    {
      "id": "mt2_001",
      "number": 1,
      "question": "Your question text here",
      "type": "single",
      "answers": [
        {"id": "mt2_001_a", "text": "Option A", "correct": true},
        {"id": "mt2_001_b", "text": "Option B", "correct": false}
      ],
      "explanation": "Brief explanation here."
    }
  ]
}
```

Restart the app after adding a new file. The dropdown will show the new label.

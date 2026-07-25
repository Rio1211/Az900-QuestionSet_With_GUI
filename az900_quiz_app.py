import html
import json
import math
import random
import re
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
QUESTION_SETS_DIR = APP_DIR / "question_sets"
QUESTIONS_FILE = APP_DIR / "questions.json"
SOURCE_HTML_FILE = APP_DIR / "az900quiz.html"
PROGRESS_FILE = APP_DIR / "progress.json"
OFFICIAL_SCORE_MAX = 1000
OFFICIAL_PASSING_SCORE = 700
EXAM_QUESTION_COUNT = 45
EXAM_DURATION_MINUTES = 45
MOCK_TEST_IDS = ("mock_test_1", "mock_test_2", "mock_test_3")


COLORS = {
    "bg": "#f5f7fb",
    "panel": "#ffffff",
    "text": "#172033",
    "muted": "#667085",
    "border": "#d9e0ea",
    "selected": "#dbeafe",
    "selected_border": "#2563eb",
    "correct": "#d1fae5",
    "correct_border": "#059669",
    "wrong": "#fee2e2",
    "wrong_border": "#dc2626",
    "button": "#1d4ed8",
    "button_text": "#ffffff",
}


def estimated_scaled_score(correct_count, question_count):
    if question_count <= 0:
        return 0
    return max(1, round((correct_count / question_count) * OFFICIAL_SCORE_MAX))


def minimum_correct_for_estimated_pass(question_count):
    return math.ceil(
        question_count * OFFICIAL_PASSING_SCORE / OFFICIAL_SCORE_MAX
    )


def clean_html(fragment):
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</p\s*>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def parse_questions_from_html(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    starts = [
        match.start()
        for match in re.finditer(
            r"<div class='step\s*'\s+data-question-id='\d+'", text
        )
    ]
    questions = []

    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else text.find(
            "<div class='ays-quiz-end-page", start
        )
        if end == -1:
            end = len(text)

        block = text[start:end]
        qid_match = re.search(r"data-question-id='(\d+)'", block)
        question_match = re.search(
            r"<div class='ays_quiz_question'>(.*?)</div>", block, re.S
        )
        if not (qid_match and question_match):
            continue

        answers = []
        answer_pattern = (
            r"name='ays_answer_correct\[\]'\s+value='([01])'.*?"
            r"<label for='[^']+' class='[^']*ays_position_initial[^']*'>"
            r"(.*?)</label>"
        )
        for answer_index, match in enumerate(re.finditer(answer_pattern, block, re.S)):
            answer_text = clean_html(match.group(2))
            if answer_text:
                answers.append(
                    {
                        "id": f"{qid_match.group(1)}_{answer_index + 1}",
                        "text": answer_text,
                        "correct": match.group(1) == "1",
                    }
                )

        explanation_match = re.search(
            r"<div class='ays_questtion_explanation' style='display:none'>"
            r"(.*?)</div>",
            block,
            re.S,
        )
        explanation = clean_html(explanation_match.group(1)) if explanation_match else ""
        question_text = clean_html(question_match.group(1))

        if question_text and answers and any(answer["correct"] for answer in answers):
            questions.append(
                {
                    "id": qid_match.group(1),
                    "number": len(questions) + 1,
                    "question": question_text,
                    "type": "single"
                    if sum(answer["correct"] for answer in answers) == 1
                    else "multiple",
                    "answers": answers,
                    "explanation": explanation,
                }
            )

    return questions


def load_legacy_questions():
    if QUESTIONS_FILE.exists():
        data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
        return data
    if SOURCE_HTML_FILE.exists():
        questions = parse_questions_from_html(SOURCE_HTML_FILE)
        QUESTIONS_FILE.write_text(
            json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return questions
    raise FileNotFoundError("Missing questions.json and az900quiz.html.")


def build_example_questions():
    examples = [
        (
            "Which Azure service provides personalized recommendations to improve "
            "cost, reliability, security, and performance?",
            ["Azure Advisor", "Azure Service Health", "Azure Monitor", "Azure Policy"],
            "Azure Advisor",
            "Azure Advisor analyzes deployed resources and provides personalized "
            "optimization recommendations.",
        ),
        (
            "Which Azure service shows personalized information about Azure service "
            "issues and planned maintenance that may affect your resources?",
            ["Azure Monitor", "Azure Service Health", "Azure Advisor", "Cost Management"],
            "Azure Service Health",
            "Azure Service Health reports active incidents, planned maintenance, and "
            "health advisories relevant to your subscriptions.",
        ),
        (
            "Which Azure service collects and analyzes metrics and logs from Azure "
            "resources and applications?",
            ["Azure Monitor", "Azure Policy", "Microsoft Purview", "Azure Arc"],
            "Azure Monitor",
            "Azure Monitor provides a common platform for collecting, analyzing, and "
            "acting on telemetry from cloud and on-premises environments.",
        ),
        (
            "What is an Azure resource group?",
            [
                "A logical container for related Azure resources",
                "A physical datacenter inside an Azure region",
                "A billing invoice for one Azure service",
                "A network connection between two regions",
            ],
            "A logical container for related Azure resources",
            "Resource groups organize resources so they can be managed, monitored, and "
            "controlled as a logical unit.",
        ),
        (
            "What is an Azure availability zone?",
            [
                "A physically separate datacenter location within an Azure region",
                "A group of subscriptions owned by one user",
                "A pricing tier for virtual machines",
                "A private connection to the Microsoft network",
            ],
            "A physically separate datacenter location within an Azure region",
            "Availability zones are separate physical locations within a region, with "
            "independent power, cooling, and networking.",
        ),
        (
            "Which cloud pricing approach charges for resources as they are consumed?",
            ["Pay-as-you-go", "Capital expenditure", "Perpetual licensing", "Fixed asset depreciation"],
            "Pay-as-you-go",
            "The consumption-based pay-as-you-go model bills for actual resource usage "
            "instead of requiring the full cost up front.",
        ),
        (
            "Which Microsoft cloud service provides identity and access management for "
            "Azure resources and applications?",
            ["Microsoft Entra ID", "Azure Monitor", "Azure Advisor", "Azure DevOps"],
            "Microsoft Entra ID",
            "Microsoft Entra ID is the cloud identity and access management service used "
            "to authenticate users and control access.",
        ),
        (
            "Which Azure service helps assess and improve the security posture of cloud "
            "resources?",
            ["Microsoft Defender for Cloud", "Azure Cost Management", "Azure DNS", "Azure Backup"],
            "Microsoft Defender for Cloud",
            "Microsoft Defender for Cloud provides security posture management and "
            "workload protection recommendations.",
        ),
        (
            "Which Azure governance service can audit resources and enforce rules such "
            "as allowed locations or required tags?",
            ["Azure Policy", "Azure Monitor", "Azure Service Health", "Azure Advisor"],
            "Azure Policy",
            "Azure Policy evaluates resources against organizational rules and can deny "
            "or remediate noncompliant configurations.",
        ),
        (
            "Which Azure feature assigns permissions to users, groups, or service "
            "principals at a selected scope?",
            [
                "Azure role-based access control (RBAC)",
                "Azure availability zones",
                "Azure Cost Management",
                "Azure Resource Manager templates",
            ],
            "Azure role-based access control (RBAC)",
            "Azure RBAC uses role assignments to grant defined permissions to a security "
            "principal at a management group, subscription, resource group, or resource scope.",
        ),
    ]

    questions = []
    for number, (question_text, options, correct_text, explanation) in enumerate(
        examples, start=1
    ):
        question_id = f"example_{number:03d}"
        questions.append(
            {
                "id": question_id,
                "number": number,
                "question": question_text,
                "type": "single",
                "answers": [
                    {
                        "id": f"{question_id}_{chr(97 + index)}",
                        "text": option,
                        "correct": option == correct_text,
                    }
                    for index, option in enumerate(options)
                ],
                "explanation": explanation,
            }
        )
    return questions


def ensure_default_question_set():
    QUESTION_SETS_DIR.mkdir(exist_ok=True)
    if any((QUESTION_SETS_DIR / f"{test_id}.json").exists() for test_id in MOCK_TEST_IDS):
        return

    example_path = QUESTION_SETS_DIR / "example_question_set.json"
    try:
        example_data = json.loads(example_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        example_data = None

    existing_questions = (
        example_data.get("questions", []) if isinstance(example_data, dict) else []
    )
    is_valid_example = (
        isinstance(example_data, dict)
        and example_data.get("label") == "Sample Test"
        and len(existing_questions) == 10
        and all(
            str(question.get("id", "")).startswith("example_")
            for question in existing_questions
        )
    )
    if not is_valid_example:
        example_data = {
            "label": "Sample Test",
            "questions": build_example_questions(),
        }
        example_path.write_text(
            json.dumps(example_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def load_question_sets():
    ensure_default_question_set()
    mock_test_paths = [
        QUESTION_SETS_DIR / f"{test_id}.json"
        for test_id in MOCK_TEST_IDS
        if (QUESTION_SETS_DIR / f"{test_id}.json").exists()
    ]
    mock_test_names = {path.name for path in mock_test_paths}
    additional_paths = sorted(
        path
        for path in QUESTION_SETS_DIR.glob("*.json")
        if path.name not in mock_test_names
        and path.name != "example_question_set.json"
    )
    question_set_paths = (mock_test_paths + additional_paths) or [
        QUESTION_SETS_DIR / "example_question_set.json"
    ]
    raw_sets = []
    for path in question_set_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            set_id = path.stem
            label = path.stem.replace("_", " ").title()
            questions = data
            question_refs = []
            include_in_exam = True
        else:
            set_id = data.get("id") or path.stem
            label = data.get("label") or path.stem.replace("_", " ").title()
            questions = data.get("questions", [])
            question_refs = data.get("question_refs", [])
            include_in_exam = data.get("include_in_exam", True)
        raw_sets.append(
            {
                "id": set_id,
                "label": label,
                "questions": questions,
                "question_refs": question_refs,
                "include_in_exam": include_in_exam,
            }
        )

    set_by_id = {}
    for question_set in raw_sets:
        set_id = question_set["id"]
        if set_id in set_by_id:
            raise ValueError(f"Duplicate question set ID: {set_id}")
        set_by_id[set_id] = question_set

    resolved_questions = {}

    def resolve_questions(question_set, resolving=()):
        set_id = question_set["id"]
        if set_id in resolved_questions:
            return resolved_questions[set_id]
        if set_id in resolving:
            chain = " -> ".join((*resolving, set_id))
            raise ValueError(f"Circular question set reference: {chain}")

        references = question_set["question_refs"]
        if not references:
            questions = list(question_set["questions"])
        else:
            questions = []
            for reference in references:
                source_set_id = reference["set_id"]
                source_question_id = str(reference["question_id"])
                source_set = set_by_id.get(source_set_id)
                if source_set is None:
                    raise ValueError(
                        f"Question set {set_id} references missing set {source_set_id}."
                    )
                source_questions = resolve_questions(source_set, (*resolving, set_id))
                question = next(
                    (
                        item
                        for item in source_questions
                        if str(item.get("id")) == source_question_id
                    ),
                    None,
                )
                if question is None:
                    raise ValueError(
                        f"Question set {set_id} references missing question "
                        f"{source_set_id}/{source_question_id}."
                    )
                questions.append(question)
        resolved_questions[set_id] = questions
        return questions

    sets = []
    for question_set in raw_sets:
        questions = resolve_questions(question_set)
        if questions:
            sets.append(
                {
                    "id": question_set["id"],
                    "label": question_set["label"],
                    "questions": questions,
                    "include_in_exam": question_set["include_in_exam"],
                }
            )
    if not sets:
        raise FileNotFoundError("No question sets found in question_sets.")
    return sets


def load_progress(question_sets):
    default = {
        "sets": {
            question_set["id"]: {
                "wrong_question_ids": [],
                "history": {},
            }
            for question_set in question_sets
        }
    }
    if not PROGRESS_FILE.exists():
        return default
    try:
        saved = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default

    if "sets" not in saved:
        first_set_id = question_sets[0]["id"]
        saved = {
            "sets": {
                first_set_id: {
                    "wrong_question_ids": saved.get("wrong_question_ids", []),
                    "history": saved.get("history", {}),
                }
            }
        }

    default.update(saved)
    for question_set in question_sets:
        set_progress = default["sets"].setdefault(
            question_set["id"], {"wrong_question_ids": [], "history": {}}
        )
        set_progress["wrong_question_ids"] = list(
            dict.fromkeys(set_progress.get("wrong_question_ids", []))
        )
        set_progress.setdefault("history", {})
    return default


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def resolve_last_location(question_sets, progress):
    """Resolve saved practice state by question ID, with safe first-item fallbacks."""
    set_by_id = {question_set["id"]: question_set for question_set in question_sets}
    first_set = question_sets[0]
    location = progress.get("last_location", {})
    if not isinstance(location, dict):
        location = {}

    saved_set_id = location.get("set_id")
    set_is_valid = saved_set_id in set_by_id
    question_set = set_by_id[saved_set_id] if set_is_valid else first_set
    questions = list(question_set["questions"])

    saved_mode = location.get("mode")
    mode_is_valid = saved_mode in ("all", "wrong")
    mode = saved_mode if set_is_valid and mode_is_valid else "all"
    if mode == "wrong":
        set_progress = progress.get("sets", {}).get(question_set["id"], {})
        wrong_ids = set(set_progress.get("wrong_question_ids", []))
        active_questions = [
            question for question in questions if question["id"] in wrong_ids
        ]
        if not active_questions:
            mode = "all"
            active_questions = list(questions)
    else:
        active_questions = list(questions)

    current_index = 0
    if set_is_valid and mode_is_valid and mode == saved_mode:
        saved_question_id = location.get("question_id")
        current_index = next(
            (
                index
                for index, question in enumerate(active_questions)
                if question["id"] == saved_question_id
            ),
            0,
        )

    return (
        question_set["id"],
        mode,
        questions,
        active_questions,
        current_index,
    )


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AZ-900 Local Question Set")
        self.geometry("980x720")
        self.minsize(820, 620)
        self.configure(bg=COLORS["bg"])

        self.question_sets = load_question_sets()
        self.set_by_id = {question_set["id"]: question_set for question_set in self.question_sets}
        self.set_id_by_label = {
            question_set["label"]: question_set["id"] for question_set in self.question_sets
        }
        self.progress = load_progress(self.question_sets)
        (
            self.current_set_id,
            self.mode,
            self.questions,
            self.active_questions,
            self.current_index,
        ) = resolve_last_location(self.question_sets, self.progress)
        self.selected_ids = set()
        self.allow_additional_answers = False
        self.checked = False
        self.session_answered = set()
        self.session_correct = 0
        self.practice_history = []
        self.option_widgets = []
        self.question_list_window = None
        self.question_list_tree = None
        self.question_search_var = None
        self.exam_answers = {}
        self.exam_deadline = None
        self.exam_timer_job = None
        self.question_image_photo = None
        self.answer_image_photo = None
        self.shuffle_locked = tk.BooleanVar(value=False)

        self._build_ui()
        self.set_selector.set(self.set_by_id[self.current_set_id]["label"])
        self.protocol("WM_DELETE_WINDOW", self.close_application)
        self.show_question()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10))

        top = ttk.Frame(self)
        top.pack(fill="x", padx=18, pady=(16, 8))

        self.title_label = ttk.Label(
            top, text="AZ-900 Practice", font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(side="left")

        selector = ttk.Frame(top)
        selector.pack(side="left", padx=(20, 0))
        ttk.Label(selector, text="Question Set").pack(side="left", padx=(0, 6))
        self.set_selector = ttk.Combobox(
            selector,
            state="readonly",
            width=22,
            values=[question_set["label"] for question_set in self.question_sets],
        )
        self.set_selector.pack(side="left")
        self.set_selector.bind("<<ComboboxSelected>>", self.change_question_set)

        actions = ttk.Frame(top)
        actions.pack(side="right")
        self.all_questions_button = ttk.Button(
            actions, text="All Questions", command=self.use_all_mode
        )
        self.all_questions_button.pack(side="left", padx=4)
        self.wrong_set_button = ttk.Button(
            actions, text="Wrong Set", command=self.use_wrong_mode
        )
        self.wrong_set_button.pack(side="left", padx=4)
        self.shuffle_button = ttk.Button(
            actions, text="Shuffle", command=self.shuffle_questions
        )
        self.shuffle_button.pack(side="left", padx=(4, 2))
        self.shuffle_lock_toggle = ttk.Checkbutton(
            actions,
            text="Lock",
            variable=self.shuffle_locked,
            command=self.update_shuffle_lock,
        )
        self.shuffle_lock_toggle.pack(side="left", padx=(0, 4))
        self.reset_button = ttk.Button(
            actions, text="Reset Session", command=self.reset_session
        )
        self.reset_button.pack(side="left", padx=4)

        self.status_label = ttk.Label(
            self, text="", font=("Segoe UI", 10), foreground=COLORS["muted"]
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))

        self.card = tk.Frame(
            self,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.card.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.card.columnconfigure(0, weight=1)
        self.card.rowconfigure(0, weight=1)

        self.content_canvas = tk.Canvas(
            self.card,
            bg=COLORS["panel"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.content_canvas.grid(row=0, column=0, sticky="nsew")

        content_scroll = ttk.Scrollbar(
            self.card, orient="vertical", command=self.content_canvas.yview
        )
        content_scroll.grid(row=0, column=1, sticky="ns")
        self.content_canvas.configure(yscrollcommand=content_scroll.set)

        self.content = tk.Frame(self.content_canvas, bg=COLORS["panel"])
        self.content_window = self.content_canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.columnconfigure(0, weight=1)
        self.content.bind("<Configure>", self._update_content_scrollregion)
        self.content_canvas.bind("<Configure>", self._resize_content)
        self.bind("<MouseWheel>", self._scroll_content, add="+")
        self.bind("<Button-4>", self._scroll_content, add="+")
        self.bind("<Button-5>", self._scroll_content, add="+")

        question_box = tk.Frame(self.content, bg=COLORS["panel"])
        question_box.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        question_box.columnconfigure(0, weight=1)

        self.question_text = tk.Text(
            question_box,
            height=5,
            wrap="word",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            relief="flat",
            borderwidth=0,
            padx=0,
            pady=0,
            font=("Segoe UI", 13, "bold"),
        )
        self.question_text.grid(row=0, column=0, sticky="ew")
        self.question_text.configure(state="disabled")

        question_scroll = ttk.Scrollbar(
            question_box, orient="vertical", command=self.question_text.yview
        )
        question_scroll.grid(row=0, column=1, sticky="ns")
        self.question_text.configure(yscrollcommand=question_scroll.set)

        answer_controls = tk.Frame(question_box, bg=COLORS["panel"])
        answer_controls.grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )
        self.additional_answer_button = ttk.Button(
            answer_controls,
            text="Add Another Answer",
            command=self.enable_additional_answers,
        )
        self.additional_answer_button.pack(side="left")
        self.additional_answer_button.state(["disabled"])
        self.reveal_button = ttk.Button(
            answer_controls,
            text="Reveal Correct Answer(s)",
            command=self.reveal_correct_answers,
        )
        self.reveal_button.pack(side="left", padx=(8, 0))
        self.reveal_button.state(["disabled"])

        self.visual_frame = tk.Frame(self.content, bg=COLORS["panel"])
        self.visual_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.visual_frame.columnconfigure(0, weight=1)
        self.question_image_label = tk.Label(
            self.visual_frame, bg=COLORS["panel"], borderwidth=0
        )
        self.question_image_label.grid(row=0, column=0)
        self.visual_frame.grid_remove()

        self.options_frame = tk.Frame(self.content, bg=COLORS["panel"])
        self.options_frame.grid(row=2, column=0, sticky="ew", padx=20)
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.bind("<Configure>", self._resize_option_wrap)

        self.feedback_frame = tk.Frame(self.content, bg=COLORS["panel"])
        self.feedback_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 14))
        self.feedback_frame.columnconfigure(0, weight=1)
        self.feedback_frame.grid_remove()

        bottom = tk.Frame(self.card, bg=COLORS["panel"])
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=14)
        bottom.columnconfigure(3, weight=1)

        self.result_label = tk.Label(
            self.feedback_frame,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            anchor="w",
            font=("Segoe UI", 11, "bold"),
        )
        self.result_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.explanation_text = tk.Text(
            self.feedback_frame,
            height=7,
            wrap="word",
            bg="#f8fafc",
            fg=COLORS["text"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            font=("Segoe UI", 10),
        )
        self.answer_image_label = tk.Label(
            self.feedback_frame, bg=COLORS["panel"], borderwidth=0
        )
        self.answer_image_label.grid(row=1, column=0, pady=(0, 8))
        self.answer_image_label.grid_remove()

        self.explanation_text.grid(row=2, column=0, sticky="ew")
        self.explanation_text.configure(state="disabled")
        explanation_scroll = ttk.Scrollbar(
            self.feedback_frame,
            orient="vertical",
            command=self.explanation_text.yview,
        )
        explanation_scroll.grid(row=2, column=1, sticky="ns")
        self.explanation_text.configure(yscrollcommand=explanation_scroll.set)

        self.visual_assessment_frame = ttk.Frame(self.feedback_frame)
        self.visual_assessment_frame.grid(row=3, column=0, sticky="w", pady=(10, 0))
        ttk.Label(self.visual_assessment_frame, text="Self-assessment:").pack(
            side="left", padx=(0, 8)
        )
        self.visual_correct_button = ttk.Button(
            self.visual_assessment_frame,
            text="I was correct",
            command=lambda: self.record_visual_self_assessment(True),
        )
        self.visual_correct_button.pack(side="left", padx=(0, 8))
        self.visual_wrong_button = ttk.Button(
            self.visual_assessment_frame,
            text="I was wrong",
            command=lambda: self.record_visual_self_assessment(False),
        )
        self.visual_wrong_button.pack(side="left")
        self.visual_assessment_frame.grid_remove()

        ttk.Button(bottom, text="Previous", command=self.previous_question).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(bottom, text="Question List", command=self.open_question_list).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        self.back_button = ttk.Button(
            bottom, text="Back to Last View", command=self.go_back_to_previous_view
        )
        self.back_button.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.back_button.state(["disabled"])
        self.check_button = ttk.Button(bottom, text="Check", command=self.check_answer)
        self.check_button.grid(
            row=0, column=3, sticky="e", padx=4
        )
        self.next_button = ttk.Button(bottom, text="Next", command=self.next_question)
        self.next_button.grid(
            row=0, column=4, sticky="e", padx=4
        )
        self.finish_button = ttk.Button(
            bottom, text="Finish / Rate", command=self.show_rate
        )
        self.finish_button.grid(
            row=0, column=5, sticky="e", padx=4
        )

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=18, pady=(0, 12))
        self.exam_button = ttk.Button(
            footer, text="Start Exam (45 min)", command=self.toggle_exam_mode
        )
        self.exam_button.pack(side="left")
        self.timer_label = ttk.Label(
            footer, text="", font=("Segoe UI", 11, "bold")
        )
        self.timer_label.pack(side="left", padx=16)
        self.clear_wrong_button = ttk.Button(
            footer, text="Clear Wrong Set", command=self.clear_wrong_set
        )
        self.clear_wrong_button.pack(side="right")

    def _update_content_scrollregion(self, _event=None):
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _resize_content(self, event):
        self.content_canvas.itemconfigure(self.content_window, width=event.width)

    def _scroll_content(self, event):
        if event.widget in (self.question_text, self.explanation_text):
            first, last = event.widget.yview()
            scrolling_up = getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4
            if (scrolling_up and first > 0) or (not scrolling_up and last < 1):
                return None

        delta = getattr(event, "delta", 0)
        if delta:
            direction = -1 if delta > 0 else 1
            units = direction * max(1, abs(delta) // 120)
        else:
            units = -1 if getattr(event, "num", 0) == 4 else 1
        self.content_canvas.yview_scroll(units, "units")
        return "break"

    def _resize_option_wrap(self, event=None):
        width = event.width if event else self.options_frame.winfo_width()
        wraplength = max(200, width - 32)
        for button, _answer in self.option_widgets:
            button.configure(wraplength=wraplength)

    def update_shuffle_lock(self):
        if self.mode == "exam" or self.shuffle_locked.get():
            self.shuffle_button.state(["disabled"])
        else:
            self.shuffle_button.state(["!disabled"])

    def show_image(self, label, relative_path, photo_attribute):
        if not relative_path:
            label.grid_remove()
            setattr(self, photo_attribute, None)
            return False
        image_path = APP_DIR / relative_path
        if not image_path.exists():
            label.grid_remove()
            setattr(self, photo_attribute, None)
            return False
        try:
            photo = tk.PhotoImage(file=str(image_path))
        except tk.TclError:
            label.grid_remove()
            setattr(self, photo_attribute, None)
            return False
        label.configure(image=photo)
        label.grid()
        setattr(self, photo_attribute, photo)
        return True

    def toggle_exam_mode(self):
        if self.mode != "exam":
            self.start_exam()
            return
        if messagebox.askyesno(
            "Exit Exam",
            "Exit the exam and discard the current exam answers?",
        ):
            self.finish_exam_mode()

    def build_exam_questions(self):
        pools = []
        for question_set in self.question_sets:
            if not question_set.get("include_in_exam", True):
                continue
            questions = []
            for original in question_set["questions"]:
                if original.get("type") == "visual_review":
                    continue
                if not original.get("answers") or not any(
                    answer.get("correct") for answer in original["answers"]
                ):
                    continue
                question = dict(original)
                question["_source_set_id"] = question_set["id"]
                question["_source_set_label"] = question_set["label"]
                question["_exam_key"] = f"{question_set['id']}:{question['id']}"
                questions.append(question)
            random.shuffle(questions)
            pools.append(questions)

        selected = []
        while len(selected) < EXAM_QUESTION_COUNT:
            available_pools = [pool for pool in pools if pool]
            if not available_pools:
                break
            random.shuffle(available_pools)
            for pool in available_pools:
                if len(selected) >= EXAM_QUESTION_COUNT:
                    break
                selected.append(pool.pop())

        random.shuffle(selected)
        return selected

    def start_exam(self, confirm=True):
        total_questions = sum(
            sum(
                question.get("type") != "visual_review"
                and bool(question.get("answers"))
                and any(answer.get("correct") for answer in question["answers"])
                for question in question_set["questions"]
            )
            for question_set in self.question_sets
            if question_set.get("include_in_exam", True)
        )
        if total_questions < EXAM_QUESTION_COUNT:
            messagebox.showerror(
                "Exam Mode",
                f"Exam mode needs at least {EXAM_QUESTION_COUNT} questions. "
                f"Only {total_questions} are currently available.",
            )
            return

        if confirm and not messagebox.askyesno(
            "Start Exam",
            f"Start a {EXAM_DURATION_MINUTES}-minute exam with "
            f"{EXAM_QUESTION_COUNT} random questions?\n\n"
            "Correctness will stay hidden until the exam is submitted.\n"
            f"Practice pass target: {minimum_correct_for_estimated_pass(EXAM_QUESTION_COUNT)}"
            f"/{EXAM_QUESTION_COUNT} questions (estimated {OFFICIAL_PASSING_SCORE}"
            f"/{OFFICIAL_SCORE_MAX}).",
        ):
            return

        self.exam_answers = {}
        self.active_questions = self.build_exam_questions()
        self.mode = "exam"
        self.current_index = 0
        self.session_answered.clear()
        self.session_correct = 0
        self.exam_deadline = time.monotonic() + EXAM_DURATION_MINUTES * 60
        self.set_exam_controls(True)
        self.show_question()
        self.update_exam_timer()

    def set_exam_controls(self, active):
        locked_buttons = (
            self.all_questions_button,
            self.wrong_set_button,
            self.back_button,
            self.shuffle_button,
            self.reset_button,
            self.clear_wrong_button,
            self.reveal_button,
        )
        if active:
            self.set_selector.configure(state="disabled")
            for button in locked_buttons:
                button.state(["disabled"])
            self.shuffle_lock_toggle.state(["disabled"])
            self.check_button.state(["disabled"])
            self.finish_button.configure(text="Submit Exam")
            self.exam_button.configure(text="Exit Exam")
        else:
            self.set_selector.configure(state="readonly")
            for button in locked_buttons:
                button.state(["!disabled"])
            self.shuffle_lock_toggle.state(["!disabled"])
            self.update_shuffle_lock()
            self.update_back_button()
            self.check_button.state(["!disabled"])
            self.finish_button.configure(text="Finish / Rate")
            self.exam_button.configure(text="Start Exam (45 min)")

    def exam_question_key(self, question):
        return question.get("_exam_key", str(question["id"]))

    def exam_time_remaining(self):
        if self.exam_deadline is None:
            return 0
        return max(0, math.ceil(self.exam_deadline - time.monotonic()))

    def format_exam_time(self):
        minutes, seconds = divmod(self.exam_time_remaining(), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_exam_timer(self):
        self.exam_timer_job = None
        if self.mode != "exam":
            return

        remaining = self.exam_time_remaining()
        self.timer_label.configure(
            text=f"Time left: {self.format_exam_time()}",
            foreground=COLORS["wrong_border"] if remaining <= 300 else COLORS["text"],
        )
        self.update_status()
        if remaining <= 0:
            self.submit_exam(confirm=False, timed_out=True)
            return
        self.exam_timer_job = self.after(1000, self.update_exam_timer)

    def submit_exam(self, confirm=True, timed_out=False):
        if self.mode != "exam":
            return

        answered = sum(bool(answer) for answer in self.exam_answers.values())
        if confirm:
            should_submit = messagebox.askyesno(
                "Submit Exam",
                f"Submit the exam now?\n\nAnswered: {answered}/{len(self.active_questions)}\n"
                f"Unanswered: {len(self.active_questions) - answered}",
            )
            if self.mode != "exam" or not should_submit:
                return

        correct_count = 0
        unanswered_count = 0
        for question in self.active_questions:
            selected_ids = self.exam_answers.get(self.exam_question_key(question), set())
            correct_ids = {
                answer["id"] for answer in question["answers"] if answer["correct"]
            }
            is_correct = selected_ids == correct_ids
            if is_correct:
                correct_count += 1
            if not selected_ids:
                unanswered_count += 1
            self.record_answer(
                question,
                is_correct,
                set_id=question["_source_set_id"],
                save=False,
            )

        save_progress(self.progress)
        question_count = len(self.active_questions)
        rate = (correct_count / question_count) * 100
        scaled_score = estimated_scaled_score(correct_count, question_count)
        status = "PASS" if scaled_score >= OFFICIAL_PASSING_SCORE else "NOT PASS"
        wrong_count = question_count - correct_count
        title = "Exam Time Expired" if timed_out else "Exam Result"
        result_message = (
            f"Correct: {correct_count}/{question_count}\n"
            f"Accuracy: {rate:.1f}%\n"
            f"Estimated scaled score: {scaled_score}/{OFFICIAL_SCORE_MAX}\n"
            f"Result: {status}\n"
            f"Incorrect: {wrong_count}\n"
            f"Unanswered: {unanswered_count}\n"
            f"Microsoft passing score: {OFFICIAL_PASSING_SCORE}/{OFFICIAL_SCORE_MAX}\n\n"
            "Practice estimate only. The real Microsoft exam uses scaled scoring, "
            "so 700 does not necessarily equal 70% correct."
        )

        self.finish_exam_mode()
        messagebox.showinfo(title, result_message)

    def finish_exam_mode(self):
        if self.exam_timer_job is not None:
            self.after_cancel(self.exam_timer_job)
            self.exam_timer_job = None
        self.exam_deadline = None
        self.exam_answers = {}
        self.mode = "all"
        self.active_questions = list(self.questions)
        self.current_index = 0
        self.set_exam_controls(False)
        self.timer_label.configure(text="")
        self.show_question()

    def open_question_list(self):
        if not self.active_questions:
            messagebox.showinfo(
                "Question List", "There are no questions in the current mode."
            )
            return

        if self.question_list_window and self.question_list_window.winfo_exists():
            self.question_list_window.lift()
            self.question_list_window.focus_force()
            return

        window = tk.Toplevel(self)
        self.question_list_window = window
        window.title("Question List")
        window.geometry("900x580")
        window.minsize(650, 420)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self.close_question_list)
        window.grab_set()
        window.columnconfigure(0, weight=1)
        window.rowconfigure(2, weight=1)

        set_label = (
            "All Question Sets"
            if self.mode == "exam"
            else self.set_by_id[self.current_set_id]["label"]
        )
        if self.mode == "exam":
            mode_label = "Exam Mode"
        elif self.mode == "wrong":
            mode_label = "Wrong Question Set"
        else:
            mode_label = "All Questions"
        ttk.Label(
            window,
            text=f"{set_label} | {mode_label} | {len(self.active_questions)} questions",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))

        search_frame = ttk.Frame(window)
        search_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Search number or text").grid(
            row=0, column=0, padx=(0, 8)
        )
        self.question_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.question_search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        self.question_search_var.trace_add("write", self.refresh_question_list)

        list_frame = ttk.Frame(window)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=16)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            list_frame,
            columns=("number", "source", "status", "question"),
            show="headings",
            selectmode="browse",
        )
        self.question_list_tree = tree
        tree.heading("number", text="#")
        tree.heading("source", text="Question Set")
        tree.heading("status", text="Status")
        tree.heading("question", text="Question")
        tree.column("number", width=60, minwidth=50, anchor="center", stretch=False)
        tree.column("source", width=130, minwidth=100, anchor="w", stretch=False)
        tree.column("status", width=110, minwidth=90, anchor="center", stretch=False)
        tree.column("question", width=520, minwidth=260, anchor="w")
        tree.tag_configure("current", background=COLORS["selected"])
        tree.tag_configure("wrong", background=COLORS["wrong"])
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.bind("<Double-1>", self.go_to_selected_question)
        tree.bind("<Return>", self.go_to_selected_question)

        buttons = ttk.Frame(window)
        buttons.grid(row=3, column=0, sticky="ew", padx=16, pady=16)
        buttons.columnconfigure(0, weight=1)
        ttk.Button(buttons, text="Close", command=self.close_question_list).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(
            buttons, text="Go to Question", command=self.go_to_selected_question
        ).grid(row=0, column=2)

        self.refresh_question_list()
        search_entry.focus_set()

    def refresh_question_list(self, *_args):
        tree = self.question_list_tree
        if not tree or not tree.winfo_exists():
            return

        search_text = (
            self.question_search_var.get().strip().lower()
            if self.question_search_var
            else ""
        )
        existing_items = tree.get_children()
        if existing_items:
            tree.delete(*existing_items)
        if self.mode == "exam":
            wrong_ids = set()
            history = {}
        else:
            set_progress = self.current_set_progress()
            wrong_ids = set(set_progress.get("wrong_question_ids", []))
            history = set_progress.get("history", {})

        for index, question in enumerate(self.active_questions):
            question_text = " ".join(question["question"].split())
            question_number = index + 1
            source_label = question.get(
                "_source_set_label", self.set_by_id[self.current_set_id]["label"]
            )
            number_match = search_text.isdigit() and int(search_text) == question_number
            text_match = search_text in question_text.lower() or search_text in source_label.lower()
            if search_text and not number_match and not text_match:
                continue

            question_id = question["id"]
            tags = ()
            if index == self.current_index:
                status = "Current"
                tags = ("current",)
            elif self.mode == "exam" and self.exam_answers.get(
                self.exam_question_key(question)
            ):
                status = "Answered"
            elif question_id in wrong_ids:
                status = "Wrong"
                tags = ("wrong",)
            elif question_id in self.session_answered:
                status = "Answered"
            elif history.get(question_id, {}).get("attempts", 0):
                status = "Practiced"
            else:
                status = "Not answered"

            tree.insert(
                "",
                "end",
                iid=str(index),
                values=(question_number, source_label, status, question_text),
                tags=tags,
            )

        current_item = str(self.current_index)
        if tree.exists(current_item):
            tree.selection_set(current_item)
            tree.focus(current_item)
            tree.see(current_item)

    def go_to_selected_question(self, _event=None):
        tree = self.question_list_tree
        if not tree or not tree.winfo_exists():
            return
        selected = tree.selection()
        if not selected:
            messagebox.showinfo(
                "Question List",
                "Select a question first.",
                parent=self.question_list_window,
            )
            return

        selected_index = int(selected[0])
        self.close_question_list()
        self.current_index = selected_index
        self.show_question()
        self.save_last_location()
        self.lift()
        self.focus_force()

    def close_question_list(self):
        if self.question_list_window and self.question_list_window.winfo_exists():
            self.question_list_window.destroy()
        self.question_list_window = None
        self.question_list_tree = None
        self.question_search_var = None

    def current_question(self):
        if not self.active_questions:
            return None
        return self.active_questions[self.current_index]

    def current_set_progress(self):
        return self.progress_for_set(self.current_set_id)

    def progress_for_set(self, set_id):
        return self.progress["sets"].setdefault(
            set_id, {"wrong_question_ids": [], "history": {}}
        )

    def current_practice_location(self):
        if self.mode not in ("all", "wrong"):
            return None
        question = self.current_question()
        return {
            "set_id": self.current_set_id,
            "mode": self.mode,
            "question_id": question["id"] if question is not None else None,
        }

    def remember_set_location(self, location):
        if location is None:
            return
        set_progress = self.progress_for_set(location["set_id"])
        set_progress["last_view"] = {
            "mode": location["mode"],
            "question_id": location["question_id"],
        }

    def saved_set_location(self, set_id):
        saved_view = self.progress_for_set(set_id).get("last_view", {})
        if not isinstance(saved_view, dict):
            saved_view = {}
        return {
            "set_id": set_id,
            "mode": saved_view.get("mode", "all"),
            "question_id": saved_view.get("question_id"),
        }

    def restore_set_location(self, set_id):
        restore_progress = dict(self.progress)
        restore_progress["last_location"] = self.saved_set_location(set_id)
        (
            self.current_set_id,
            self.mode,
            self.questions,
            self.active_questions,
            self.current_index,
        ) = resolve_last_location(self.question_sets, restore_progress)

    def capture_practice_state(self):
        location = self.current_practice_location()
        if location is None:
            return None
        return {
            "location": location,
            "session_answered": set(self.session_answered),
            "session_correct": self.session_correct,
        }

    def remember_practice_state(self, state):
        if state is None or state["location"] == self.current_practice_location():
            return
        if (
            self.practice_history
            and self.practice_history[-1]["location"] == state["location"]
        ):
            self.practice_history[-1] = state
        else:
            self.practice_history.append(state)
        self.update_back_button()

    def update_back_button(self):
        if self.mode == "exam" or not self.practice_history:
            self.back_button.state(["disabled"])
        else:
            self.back_button.state(["!disabled"])

    def go_back_to_previous_view(self):
        if self.mode == "exam" or not self.practice_history:
            return

        state = self.practice_history.pop()
        restore_progress = dict(self.progress)
        restore_progress["last_location"] = state["location"]
        previous_set_id = self.current_set_id
        (
            self.current_set_id,
            self.mode,
            self.questions,
            self.active_questions,
            self.current_index,
        ) = resolve_last_location(self.question_sets, restore_progress)
        if self.current_set_id != previous_set_id:
            self.session_answered = set(state["session_answered"])
            self.session_correct = state["session_correct"]
        self.set_selector.set(self.set_by_id[self.current_set_id]["label"])
        self.show_question()
        self.save_last_location()
        self.update_back_button()

    def save_last_location(self):
        location = self.current_practice_location()
        if location is None:
            return
        self.remember_set_location(location)
        self.progress["last_location"] = location
        save_progress(self.progress)

    def close_application(self):
        self.save_last_location()
        self.destroy()

    def set_question_text(self, text):
        self.question_text.configure(state="normal")
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", text)
        self.question_text.configure(state="disabled")

    def show_question(self):
        question = self.current_question()
        self.selected_ids = set()
        self.allow_additional_answers = False
        self.checked = False
        self.result_label.config(text="")
        self.set_explanation("")
        self.feedback_frame.grid_remove()
        self.visual_frame.grid_remove()
        self.question_image_label.grid_remove()
        self.answer_image_label.grid_remove()
        self.visual_assessment_frame.grid_remove()
        self.question_image_photo = None
        self.answer_image_photo = None
        self.visual_correct_button.state(["!disabled"])
        self.visual_wrong_button.state(["!disabled"])
        if self.mode != "exam":
            self.check_button.configure(text="Check")
            self.check_button.state(["!disabled"])
        self.content_canvas.yview_moveto(0)

        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.option_widgets = []

        if question is None:
            self.update_additional_answer_button(None)
            self.update_reveal_button(None)
            self.set_question_text(
                "No questions in this mode. Answer questions incorrectly first, or switch back to All Questions."
            )
            self.update_status()
            return

        if self.mode == "exam":
            self.selected_ids = set(
                self.exam_answers.get(self.exam_question_key(question), set())
            )
            source_text = f" | {question['_source_set_label']}"
        else:
            source_text = ""
        self.allow_additional_answers = (
            question.get("type") == "multiple" or len(self.selected_ids) > 1
        )
        self.update_additional_answer_button(question)
        self.update_reveal_button(question)
        self.set_question_text(
            f"Question {self.current_index + 1} of {len(self.active_questions)}"
            f"{source_text}\n{question['question']}"
        )

        if self.show_image(
            self.question_image_label,
            question.get("question_image"),
            "question_image_photo",
        ):
            self.visual_frame.grid()

        if question.get("type") == "visual_review":
            self.check_button.configure(text="Reveal Answer")

        for row, answer in enumerate(question["answers"]):
            button = tk.Button(
                self.options_frame,
                text=answer["text"],
                anchor="w",
                justify="left",
                wraplength=860,
                relief="solid",
                bd=1,
                padx=12,
                pady=10,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                activebackground=COLORS["selected"],
                font=("Segoe UI", 10),
                command=lambda answer_id=answer["id"]: self.select_answer(answer_id),
            )
            button.grid(row=row, column=0, sticky="ew", pady=5)
            self.option_widgets.append((button, answer))

        self._resize_option_wrap()
        self.paint_options()

        self.update_status()

    def update_additional_answer_button(self, question):
        can_enable = (
            question is not None
            and question.get("type") != "visual_review"
            and len(question.get("answers", [])) > 1
            and not self.checked
        )
        if self.allow_additional_answers:
            self.additional_answer_button.configure(text="Multiple Answers Enabled")
            self.additional_answer_button.state(["disabled"])
        else:
            self.additional_answer_button.configure(text="Add Another Answer")
            if can_enable:
                self.additional_answer_button.state(["!disabled"])
            else:
                self.additional_answer_button.state(["disabled"])

    def update_reveal_button(self, question):
        can_reveal = (
            self.mode != "exam"
            and question is not None
            and question.get("type") != "visual_review"
            and bool(question.get("answers"))
            and not self.checked
        )
        if can_reveal:
            self.reveal_button.state(["!disabled"])
        else:
            self.reveal_button.state(["disabled"])

    def enable_additional_answers(self):
        question = self.current_question()
        if question is None or self.checked:
            return
        if question.get("type") == "visual_review":
            return
        self.allow_additional_answers = True
        self.update_additional_answer_button(question)

    def select_answer(self, answer_id):
        if self.checked:
            return
        question = self.current_question()
        if question["type"] == "single" and not self.allow_additional_answers:
            self.selected_ids = {answer_id}
        elif answer_id in self.selected_ids:
            self.selected_ids.remove(answer_id)
        else:
            self.selected_ids.add(answer_id)
        if self.mode == "exam":
            self.exam_answers[self.exam_question_key(question)] = set(self.selected_ids)
        self.paint_options()
        self.update_status()

    def paint_options(self):
        for button, answer in self.option_widgets:
            bg = COLORS["panel"]
            border = COLORS["border"]
            if self.checked:
                if answer["correct"]:
                    bg = COLORS["correct"]
                    border = COLORS["correct_border"]
                elif answer["id"] in self.selected_ids:
                    bg = COLORS["wrong"]
                    border = COLORS["wrong_border"]
            elif answer["id"] in self.selected_ids:
                bg = COLORS["selected"]
                border = COLORS["selected_border"]
            button.config(bg=bg, highlightbackground=border, highlightcolor=border)

    def check_answer(self):
        if self.mode == "exam":
            return
        question = self.current_question()
        if question is None:
            return
        if question.get("type") == "visual_review":
            self.reveal_visual_answer(question)
            return
        if not self.selected_ids:
            messagebox.showinfo("Select an answer", "Choose an option first.")
            return

        correct_ids = {answer["id"] for answer in question["answers"] if answer["correct"]}
        is_correct = self.selected_ids == correct_ids
        self.checked = True
        self.update_additional_answer_button(question)
        self.update_reveal_button(question)
        self.paint_options()

        if question["id"] not in self.session_answered:
            self.session_answered.add(question["id"])
            if is_correct:
                self.session_correct += 1

        self.record_answer(question, is_correct)
        self.result_label.config(
            text="Correct." if is_correct else "Incorrect. Review the highlighted answer."
        )
        self.set_explanation(self.build_explanation(question, is_correct))
        self.feedback_frame.grid()
        self._update_content_scrollregion()
        self.update_status()

    def reveal_correct_answers(self):
        if self.mode == "exam" or self.checked:
            return
        question = self.current_question()
        if question is None:
            return
        if question.get("type") == "visual_review":
            self.reveal_visual_answer(question)
            return

        self.checked = True
        self.update_additional_answer_button(question)
        self.update_reveal_button(question)
        self.check_button.state(["disabled"])
        self.paint_options()
        self.result_label.config(
            text="Correct answer revealed. This was not recorded as an attempt."
        )
        self.set_explanation(
            self.build_explanation(question, False, include_selected=False)
        )
        self.feedback_frame.grid()
        self._update_content_scrollregion()
        self.update_status()

    def reveal_visual_answer(self, question):
        if self.checked:
            return
        self.checked = True
        self.update_reveal_button(question)
        answer_shown = self.show_image(
            self.answer_image_label,
            question.get("answer_image"),
            "answer_image_photo",
        )
        if answer_shown:
            self.result_label.config(
                text="Source PDF answer revealed. Compare it with your answer."
            )
        else:
            self.result_label.config(
                text="The PDF has no separate answer image for this visual question."
            )
        self.set_explanation(self.build_explanation(question, False))
        self.visual_assessment_frame.grid()
        self.feedback_frame.grid()
        self._update_content_scrollregion()

    def record_visual_self_assessment(self, is_correct):
        question = self.current_question()
        if not question or question.get("type") != "visual_review":
            return
        if question["id"] not in self.session_answered:
            self.session_answered.add(question["id"])
            if is_correct:
                self.session_correct += 1
            self.record_answer(question, is_correct)
        self.visual_correct_button.state(["disabled"])
        self.visual_wrong_button.state(["disabled"])
        self.result_label.config(
            text=(
                "Recorded as correct."
                if is_correct
                else "Recorded as wrong and added to the wrong-question set."
            )
        )
        self.update_status()

    def record_answer(self, question, is_correct, set_id=None, save=True):
        qid = question["id"]
        set_progress = self.progress_for_set(set_id or self.current_set_id)
        history = set_progress.setdefault("history", {}).setdefault(
            qid, {"attempts": 0, "correct": 0, "wrong": 0}
        )
        history["attempts"] += 1
        if is_correct:
            history["correct"] += 1
            if qid in set_progress["wrong_question_ids"]:
                set_progress["wrong_question_ids"].remove(qid)
        else:
            history["wrong"] += 1
            if qid not in set_progress["wrong_question_ids"]:
                set_progress["wrong_question_ids"].append(qid)
        if save:
            save_progress(self.progress)

    def build_explanation(self, question, is_correct, include_selected=True):
        if question.get("type") == "visual_review":
            lines = [
                "This visual question is self-assessed because its interaction is image-based.",
                "The revealed image and explanation come from the source PDF and may be disputed.",
            ]
            if question.get("explanation"):
                lines.extend(("", question["explanation"]))
            self.append_community_votes(lines, question)
            return "\n".join(lines)

        correct_answers = [
            answer["text"] for answer in question["answers"] if answer["correct"]
        ]
        selected_answers = [
            answer["text"]
            for answer in question["answers"]
            if answer["id"] in self.selected_ids
        ]
        lines = []
        if include_selected:
            lines.append(f"Your answer: {', '.join(selected_answers)}")
        lines.append(
            f"Source PDF answer: {', '.join(correct_answers)}"
            if question.get("source_answer_unverified")
            else f"Correct answer: {', '.join(correct_answers)}"
        )
        if question.get("explanation"):
            lines.append("")
            lines.append(question["explanation"])
        else:
            lines.append("")
            if question.get("source_answer_unverified"):
                lines.append(
                    "Why: the source PDF marks the highlighted option as its answer. "
                    "Use the community percentages below to identify potentially disputed answers."
                )
            else:
                lines.append(
                    "Why: the local source HTML marks the highlighted option as correct. "
                    "The other choices are marked incorrect in the same source question."
                )
                lines.append(
                    "Tip: edit the active file in question_sets if you want to add your own detailed AZ-900 explanation for this question."
                )
        self.append_community_votes(lines, question)
        return "\n".join(lines)

    def append_community_votes(self, lines, question):
        if "community_votes" not in question:
            return
        lines.extend(("", "Community vote distribution from the source PDF:"))
        votes = question.get("community_votes", [])
        if not votes:
            lines.append("Not available for this question.")
            return

        if all(len(vote["choice"]) == 1 for vote in votes):
            vote_by_choice = {
                vote["choice"]: vote["percentage"] for vote in votes
            }
            for answer in question.get("answers", []):
                choice = answer.get("label", "?")
                percentage = vote_by_choice.get(choice)
                display = f"{percentage}%" if percentage is not None else "not shown"
                lines.append(f"{choice}. {answer['text']}: {display}")
        else:
            for vote in votes:
                lines.append(f"Choice combination {vote['choice']}: {vote['percentage']}%")
            lines.append("The PDF poll reports answer combinations for this multi-select question.")
        lines.append("Community votes are informal and are not an official Microsoft answer key.")

    def set_explanation(self, text):
        self.explanation_text.configure(state="normal")
        self.explanation_text.delete("1.0", "end")
        self.explanation_text.insert("1.0", text)
        self.explanation_text.yview_moveto(0)
        self.explanation_text.configure(state="disabled")

    def next_question(self):
        if not self.active_questions:
            return
        if self.current_index < len(self.active_questions) - 1:
            self.current_index += 1
            self.show_question()
            self.save_last_location()
        else:
            self.show_rate()

    def previous_question(self):
        if not self.active_questions:
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()
            self.save_last_location()

    def change_question_set(self, event=None):
        selected_label = self.set_selector.get()
        selected_set_id = self.set_id_by_label.get(selected_label)
        if not selected_set_id or selected_set_id == self.current_set_id:
            return
        previous_state = self.capture_practice_state()
        if previous_state is not None:
            self.remember_set_location(previous_state["location"])
        self.restore_set_location(selected_set_id)
        self.session_answered.clear()
        self.session_correct = 0
        self.show_question()
        self.remember_practice_state(previous_state)
        self.save_last_location()

    def use_all_mode(self):
        previous_state = self.capture_practice_state()
        self.mode = "all"
        self.active_questions = list(self.questions)
        self.current_index = 0
        self.show_question()
        self.remember_practice_state(previous_state)
        self.save_last_location()

    def use_wrong_mode(self):
        previous_state = self.capture_practice_state()
        wrong_ids = set(self.current_set_progress().get("wrong_question_ids", []))
        self.mode = "wrong"
        self.active_questions = [q for q in self.questions if q["id"] in wrong_ids]
        self.current_index = 0
        self.show_question()
        self.remember_practice_state(previous_state)
        self.save_last_location()

    def shuffle_questions(self):
        if self.shuffle_locked.get() or not self.active_questions:
            return
        random.shuffle(self.active_questions)
        self.current_index = 0
        self.show_question()

    def reset_session(self):
        self.session_answered.clear()
        self.session_correct = 0
        self.current_index = 0
        self.show_question()

    def clear_wrong_set(self):
        if not messagebox.askyesno(
            "Clear wrong set", "Remove all saved wrong questions?"
        ):
            return
        self.current_set_progress()["wrong_question_ids"] = []
        save_progress(self.progress)
        if self.mode == "wrong":
            self.active_questions = []
            self.current_index = 0
        self.show_question()

    def update_status(self):
        if self.mode == "exam":
            answered = sum(bool(answer) for answer in self.exam_answers.values())
            self.status_label.config(
                text=(
                    f"Exam | Question {self.current_index + 1}/{len(self.active_questions)} "
                    f"| Answered {answered}/{len(self.active_questions)}"
                )
            )
            return

        answered = len(self.session_answered)
        scaled_score = estimated_scaled_score(self.session_correct, answered)
        wrong_count = len(self.current_set_progress().get("wrong_question_ids", []))
        mode_label = "Wrong Question Set" if self.mode == "wrong" else "All Questions"
        set_label = self.set_by_id[self.current_set_id]["label"]
        self.status_label.config(
            text=(
                f"Set: {set_label} | {mode_label} | Session: {self.session_correct}/{answered} "
                f"| Est. score: {scaled_score}/{OFFICIAL_SCORE_MAX} "
                f"| Pass: {OFFICIAL_PASSING_SCORE} | Wrong: {wrong_count}"
            )
        )

    def show_rate(self):
        if self.mode == "exam":
            self.submit_exam()
            return
        answered = len(self.session_answered)
        if answered == 0:
            messagebox.showinfo("Rate", "No checked answers in this session yet.")
            return
        rate = (self.session_correct / answered) * 100
        scaled_score = estimated_scaled_score(self.session_correct, answered)
        status = "PASS" if scaled_score >= OFFICIAL_PASSING_SCORE else "NOT PASS"
        messagebox.showinfo(
            "Practice Result",
            (
                f"Correct: {self.session_correct}/{answered}\n"
                f"Accuracy: {rate:.1f}%\n"
                f"Estimated scaled score: {scaled_score}/{OFFICIAL_SCORE_MAX}\n"
                f"Result: {status}\n"
                f"Microsoft passing score: {OFFICIAL_PASSING_SCORE}/{OFFICIAL_SCORE_MAX}\n\n"
                "Practice estimate only. The real Microsoft exam uses scaled scoring, "
                "so 700 does not necessarily equal 70% correct."
            ),
        )


def main():
    try:
        app = QuizApp()
    except Exception as exc:
        messagebox.showerror("Startup error", str(exc))
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.competitions.models import Competition, CompetitionDiscipline
from apps.studies.models import Lesson

from .forms import QuestionRecordForm
from .models import QuestionRecord


def question_list(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_links = list(
        competition.discipline_links.select_related("discipline")
        .order_by("position", "discipline__name")
    )

    questions = (
        QuestionRecord.objects.filter(
            competition_discipline__competition=competition
        )
        .select_related(
            "competition_discipline__discipline",
            "lesson",
        )
        .order_by("-answered_date", "-id")
    )

    discipline_id = request.GET.get("disciplina", "").strip()
    lesson_id = request.GET.get("aula", "").strip()
    result = request.GET.get("resultado", "").strip()
    review = request.GET.get("revisao", "").strip()
    board = request.GET.get("banca", "").strip()
    date_value = request.GET.get("data", "").strip()
    query = request.GET.get("q", "").strip()

    selected_discipline_link = None
    lessons = Lesson.objects.none()

    if discipline_id.isdigit():
        selected_discipline_link = next(
            (
                link
                for link in discipline_links
                if link.pk == int(discipline_id)
            ),
            None,
        )
        if selected_discipline_link:
            questions = questions.filter(
                competition_discipline=selected_discipline_link
            )
            lessons = Lesson.objects.filter(
                competition_discipline=selected_discipline_link
            ).order_by("position", "id")

    if lesson_id.isdigit():
        questions = questions.filter(lesson_id=int(lesson_id))

    valid_results = {value for value, _ in QuestionRecord.Result.choices}
    if result in valid_results:
        questions = questions.filter(result=result)

    if review == "required":
        questions = questions.filter(review_required=True)
    elif review == "pending":
        questions = questions.filter(
            review_required=True,
            review_status=QuestionRecord.ReviewStatus.PENDING,
        )
    elif review == "completed":
        questions = questions.filter(
            review_required=True,
            review_status=QuestionRecord.ReviewStatus.COMPLETED,
        )
    elif review == "not_required":
        questions = questions.filter(review_required=False)

    if board:
        questions = questions.filter(board__icontains=board)

    parsed_date = parse_date(date_value) if date_value else None
    if parsed_date:
        questions = questions.filter(answered_date=parsed_date)

    if query:
        questions = questions.filter(
            Q(question_number__icontains=query)
            | Q(exam_context__icontains=query)
            | Q(topic_subtopic__icontains=query)
            | Q(source__icontains=query)
            | Q(observation__icontains=query)
        )

    questions = list(questions)

    valid_questions = [
        item
        for item in questions
        if item.result != QuestionRecord.Result.NOT_COUNTED
    ]
    correct_count = sum(
        item.result == QuestionRecord.Result.CORRECT
        for item in valid_questions
    )
    incorrect_count = sum(
        item.result == QuestionRecord.Result.INCORRECT
        for item in valid_questions
    )
    accuracy = (
        round((correct_count / len(valid_questions)) * 100, 1)
        if valid_questions
        else None
    )
    pending_reviews = sum(
        item.review_required
        and item.review_status != QuestionRecord.ReviewStatus.COMPLETED
        for item in questions
    )

    boards = list(
        QuestionRecord.objects.filter(
            competition_discipline__competition=competition
        )
        .exclude(board="")
        .values_list("board", flat=True)
        .distinct()
        .order_by("board")
    )

    return render(
        request,
        "questions/question_list.html",
        {
            "competition": competition,
            "active_tab": "questions",
            "questions": questions,
            "discipline_links": discipline_links,
            "selected_discipline_link": selected_discipline_link,
            "lessons": lessons,
            "boards": boards,
            "result_choices": QuestionRecord.Result.choices,
            "filters": {
                "discipline": discipline_id,
                "lesson": lesson_id,
                "result": result,
                "review": review,
                "board": board,
                "date": date_value,
                "q": query,
            },
            "filtered_total": len(questions),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "accuracy": accuracy,
            "pending_reviews": pending_reviews,
        },
    )


def question_choose_discipline(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_links = list(
        competition.discipline_links.select_related("discipline")
        .order_by("position", "discipline__name")
    )
    return render(
        request,
        "questions/question_choose_discipline.html",
        {
            "competition": competition,
            "active_tab": "questions",
            "discipline_links": discipline_links,
        },
    )


def question_create(request, pk, link_id):
    competition = get_object_or_404(Competition, pk=pk)
    discipline_link = get_object_or_404(
        CompetitionDiscipline.objects.select_related("discipline"),
        pk=link_id,
        competition=competition,
    )

    preselected_lesson = None
    lesson_id = request.GET.get("aula", "").strip()
    if lesson_id.isdigit():
        preselected_lesson = Lesson.objects.filter(
            pk=int(lesson_id),
            competition_discipline=discipline_link,
        ).first()

    form = QuestionRecordForm(
        request.POST or None,
        discipline_link=discipline_link,
        lesson=preselected_lesson,
    )

    if request.method == "POST" and form.is_valid():
        question = form.save()
        return redirect(
            f'{reverse("questions:question_list", kwargs={"pk": competition.pk})}'
            f'?disciplina={question.competition_discipline_id}'
        )

    return render(
        request,
        "questions/question_form.html",
        {
            "competition": competition,
            "discipline_link": discipline_link,
            "form": form,
            "page_title": "Nova questão",
            "submit_label": "Salvar questão",
        },
    )


def question_edit(request, pk, question_id):
    competition = get_object_or_404(Competition, pk=pk)
    question = get_object_or_404(
        QuestionRecord.objects.select_related(
            "competition_discipline__discipline",
            "lesson",
        ),
        pk=question_id,
        competition_discipline__competition=competition,
    )
    discipline_link = question.competition_discipline

    form = QuestionRecordForm(
        request.POST or None,
        instance=question,
        discipline_link=discipline_link,
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save()
        return redirect(
            f'{reverse("questions:question_list", kwargs={"pk": competition.pk})}'
            f'?disciplina={updated.competition_discipline_id}'
        )

    return render(
        request,
        "questions/question_form.html",
        {
            "competition": competition,
            "discipline_link": discipline_link,
            "question": question,
            "form": form,
            "page_title": f"Editar {question.question_number}",
            "submit_label": "Salvar alterações",
        },
    )

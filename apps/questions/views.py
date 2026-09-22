from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.competitions.models import Competition, CompetitionDiscipline, Discipline
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
            Q(code__icontains=query)
            | Q(question_number__icontains=query)
            | Q(exam_context__icontains=query)
            | Q(topic_subtopic__icontains=query)
            | Q(source__icontains=query)
            | Q(observation__icontains=query)
        )

    metrics = questions.aggregate(
        total=Count("id"),
        correct=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.CORRECT),
        ),
        incorrect=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.INCORRECT),
        ),
        not_counted=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.NOT_COUNTED),
        ),
        pending_reviews=Count(
            "id",
            filter=Q(review_required=True)
            & ~Q(review_status=QuestionRecord.ReviewStatus.COMPLETED),
        ),
    )

    correct_count = metrics["correct"] or 0
    incorrect_count = metrics["incorrect"] or 0
    valid_total = correct_count + incorrect_count
    accuracy = (
        round((correct_count / valid_total) * 100, 1)
        if valid_total
        else None
    )
    pending_reviews = metrics["pending_reviews"] or 0

    paginator = Paginator(questions, 50)
    page_obj = paginator.get_page(request.GET.get("pagina"))
    pagination_query = request.GET.copy()
    pagination_query.pop("pagina", None)

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
            "questions": page_obj.object_list,
            "page_obj": page_obj,
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
            "filtered_total": metrics["total"] or 0,
            "not_counted_count": metrics["not_counted"] or 0,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "accuracy": accuracy,
            "pending_reviews": pending_reviews,
            "page_size": paginator.per_page,
            "pagination_query": pagination_query.urlencode(),
            "pagination_pages": paginator.get_elided_page_range(
                page_obj.number,
                on_each_side=2,
                on_ends=1,
            ),
            "pagination_ellipsis": paginator.ELLIPSIS,
        },
    )


def question_detail(request, pk, question_id):
    competition = get_object_or_404(Competition, pk=pk)
    question = get_object_or_404(
        QuestionRecord.objects.select_related(
            "competition_discipline__discipline",
            "competition_discipline__competition",
            "lesson",
        ),
        pk=question_id,
        competition_discipline__competition=competition,
    )
    return render(
        request,
        "questions/question_detail.html",
        {
            "competition": competition,
            "active_tab": "questions",
            "question": question,
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



def _global_question_filters(request, queryset):
    competition_id = request.GET.get("concurso", "").strip()
    discipline_id = request.GET.get("disciplina", "").strip()
    result = request.GET.get("resultado", "").strip()
    review = request.GET.get("revisao", "").strip()
    board = request.GET.get("banca", "").strip()
    start_date = request.GET.get("inicio", "").strip()
    end_date = request.GET.get("fim", "").strip()
    query = request.GET.get("q", "").strip()

    if competition_id.isdigit():
        queryset = queryset.filter(
            competition_discipline__competition_id=int(competition_id)
        )

    if discipline_id.isdigit():
        queryset = queryset.filter(
            competition_discipline__discipline_id=int(discipline_id)
        )

    valid_results = {value for value, _ in QuestionRecord.Result.choices}
    if result in valid_results:
        queryset = queryset.filter(result=result)

    if review == "required":
        queryset = queryset.filter(review_required=True)
    elif review == "pending":
        queryset = queryset.filter(
            review_required=True,
        ).exclude(
            review_status=QuestionRecord.ReviewStatus.COMPLETED
        )
    elif review == "completed":
        queryset = queryset.filter(
            review_required=True,
            review_status=QuestionRecord.ReviewStatus.COMPLETED,
        )
    elif review == "not_required":
        queryset = queryset.filter(review_required=False)

    if board:
        queryset = queryset.filter(board=board)

    parsed_start = parse_date(start_date) if start_date else None
    if parsed_start:
        queryset = queryset.filter(answered_date__gte=parsed_start)

    parsed_end = parse_date(end_date) if end_date else None
    if parsed_end:
        queryset = queryset.filter(answered_date__lte=parsed_end)

    if query:
        queryset = queryset.filter(
            Q(code__icontains=query)
            | Q(question_number__icontains=query)
            | Q(exam_context__icontains=query)
            | Q(topic_subtopic__icontains=query)
            | Q(source__icontains=query)
            | Q(observation__icontains=query)
            | Q(competition_discipline__competition__name__icontains=query)
            | Q(competition_discipline__discipline__name__icontains=query)
        )

    return queryset, {
        "competition": competition_id,
        "discipline": discipline_id,
        "result": result,
        "review": review,
        "board": board,
        "start": start_date,
        "end": end_date,
        "q": query,
    }


def _question_metrics(queryset):
    metrics = queryset.aggregate(
        total=Count("id"),
        correct=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.CORRECT),
        ),
        incorrect=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.INCORRECT),
        ),
        not_counted=Count(
            "id",
            filter=Q(result=QuestionRecord.Result.NOT_COUNTED),
        ),
        pending_reviews=Count(
            "id",
            filter=Q(review_required=True)
            & ~Q(review_status=QuestionRecord.ReviewStatus.COMPLETED),
        ),
    )
    valid_total = (metrics["correct"] or 0) + (metrics["incorrect"] or 0)
    metrics["accuracy"] = (
        round(((metrics["correct"] or 0) / valid_total) * 100, 1)
        if valid_total
        else None
    )
    metrics["valid_total"] = valid_total
    return metrics


def global_question_list(request):
    questions = QuestionRecord.objects.select_related(
        "competition_discipline__competition",
        "competition_discipline__discipline",
        "lesson",
    ).order_by("-answered_date", "-id")

    questions, filters = _global_question_filters(request, questions)
    metrics = _question_metrics(questions)

    paginator = Paginator(questions, 50)
    page_obj = paginator.get_page(request.GET.get("pagina"))
    pagination_query = request.GET.copy()
    pagination_query.pop("pagina", None)

    competitions = Competition.objects.order_by("name")
    disciplines = (
        Discipline.objects.filter(
            competitiondiscipline__question_records__isnull=False
        )
        .distinct()
        .order_by("name")
    )
    boards = list(
        QuestionRecord.objects.exclude(board="")
        .values_list("board", flat=True)
        .distinct()
        .order_by("board")
    )

    return render(
        request,
        "questions/global_question_list.html",
        {
            "questions": page_obj.object_list,
            "page_obj": page_obj,
            "competitions": competitions,
            "disciplines": disciplines,
            "boards": boards,
            "result_choices": QuestionRecord.Result.choices,
            "filters": filters,
            "metrics": metrics,
            "active_global_question_tab": "list",
            "page_size": paginator.per_page,
            "pagination_query": pagination_query.urlencode(),
            "pagination_pages": paginator.get_elided_page_range(
                page_obj.number,
                on_each_side=2,
                on_ends=1,
            ),
            "pagination_ellipsis": paginator.ELLIPSIS,
        },
    )


def global_question_choose_competition(request):
    competitions = Competition.objects.order_by("exam_date", "name")
    return render(
        request,
        "questions/global_question_choose_competition.html",
        {
            "competitions": competitions,
            "active_global_question_tab": "list",
        },
    )


def global_question_dashboard(request):
    questions = QuestionRecord.objects.select_related(
        "competition_discipline__competition",
        "competition_discipline__discipline",
    )
    questions, filters = _global_question_filters(request, questions)
    metrics = _question_metrics(questions)

    monthly_rows = list(
        questions.annotate(month=TruncMonth("answered_date"))
        .values("month")
        .annotate(
            total=Count("id"),
            correct=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.CORRECT),
            ),
            incorrect=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.INCORRECT),
            ),
        )
        .order_by("month")
    )
    for row in monthly_rows:
        valid = row["correct"] + row["incorrect"]
        row["accuracy"] = (
            round((row["correct"] / valid) * 100, 1)
            if valid
            else None
        )

    contest_rows = list(
        questions.values(
            "competition_discipline__competition__name"
        )
        .annotate(
            total=Count("id"),
            correct=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.CORRECT),
            ),
            incorrect=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.INCORRECT),
            ),
            first_answered=Min("answered_date"),
        )
        .order_by("first_answered", "competition_discipline__competition__name")
    )
    for row in contest_rows:
        valid = row["correct"] + row["incorrect"]
        row["accuracy"] = (
            round((row["correct"] / valid) * 100, 1)
            if valid
            else None
        )

    discipline_rows = list(
        questions.values(
            "competition_discipline__discipline__name"
        )
        .annotate(
            total=Count("id"),
            correct=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.CORRECT),
            ),
            incorrect=Count(
                "id",
                filter=Q(result=QuestionRecord.Result.INCORRECT),
            ),
        )
        .order_by("competition_discipline__discipline__name")
    )
    for row in discipline_rows:
        valid = row["correct"] + row["incorrect"]
        row["accuracy"] = (
            round((row["correct"] / valid) * 100, 1)
            if valid
            else None
        )

    competitions_with_questions = (
        questions.values(
            "competition_discipline__competition_id"
        )
        .distinct()
        .count()
    )

    chart_data = {
        "months": {
            "labels": [
                row["month"].strftime("%m/%Y")
                for row in monthly_rows
                if row["month"]
            ],
            "questions": [
                row["total"]
                for row in monthly_rows
                if row["month"]
            ],
            "accuracy": [
                row["accuracy"]
                for row in monthly_rows
                if row["month"]
            ],
        },
        "results": {
            "labels": ["Acertos", "Erros", "Não contabilizadas"],
            "values": [
                metrics["correct"] or 0,
                metrics["incorrect"] or 0,
                metrics["not_counted"] or 0,
            ],
        },
        "contests": {
            "labels": [
                row["competition_discipline__competition__name"]
                for row in contest_rows
            ],
            "questions": [row["total"] for row in contest_rows],
            "accuracy": [row["accuracy"] for row in contest_rows],
        },
        "disciplines": {
            "labels": [
                row["competition_discipline__discipline__name"]
                for row in discipline_rows
            ],
            "questions": [row["total"] for row in discipline_rows],
            "accuracy": [row["accuracy"] for row in discipline_rows],
        },
    }

    competitions = Competition.objects.order_by("name")
    disciplines = (
        Discipline.objects.filter(
            competitiondiscipline__question_records__isnull=False
        )
        .distinct()
        .order_by("name")
    )
    boards = list(
        QuestionRecord.objects.exclude(board="")
        .values_list("board", flat=True)
        .distinct()
        .order_by("board")
    )

    return render(
        request,
        "questions/global_question_dashboard.html",
        {
            "metrics": metrics,
            "competitions_with_questions": competitions_with_questions,
            "competitions": competitions,
            "disciplines": disciplines,
            "boards": boards,
            "result_choices": QuestionRecord.Result.choices,
            "filters": filters,
            "chart_data": chart_data,
            "contest_rows": contest_rows,
            "active_global_question_tab": "dashboard",
        },
    )

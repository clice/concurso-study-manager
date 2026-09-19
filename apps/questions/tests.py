from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.competitions.models import (
    Competition,
    CompetitionDiscipline,
    Discipline,
    ExamBoard,
)
from apps.studies.models import Lesson

from .forms import QuestionRecordForm
from .models import QuestionRecord


class QuestionRecordTests(TestCase):
    def setUp(self):
        board, _ = ExamBoard.objects.get_or_create(
            acronym="FGV",
            defaults={"name": "Fundação Getulio Vargas"},
        )
        self.competition = Competition.objects.create(
            name="DATAPREV 2026",
            organization="DATAPREV",
            role="ATI — Desenvolvimento de Software",
            board=board,
            status=Competition.Status.ACTIVE,
        )
        systems = Discipline.objects.create(name="Desenvolvimento de Sistemas")
        portuguese = Discipline.objects.create(name="Língua Portuguesa")
        self.systems_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.portuguese_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=portuguese,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.GENERAL,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.junit = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="6 - JUnit II",
        )
        self.portuguese_lesson = Lesson.objects.create(
            competition_discipline=self.portuguese_link,
            title="Classes de Palavras",
        )

    def payload(self, **overrides):
        payload = {
            "lesson": str(self.junit.pk),
            "answered_date": "2026-09-02",
            "board": "FGV",
            "exam_context": "AL-GO — Analista Legislativo / Desenvolvedor de Sistemas — 2026",
            "question_number": "Slides Q01 — G588",
            "topic_subtopic": "Testes de Software — JUnit",
            "user_answer": "E",
            "answer_key": "B",
            "result": QuestionRecord.Result.INCORRECT,
            "source": "Slides G588 — 6 - JUnit II",
            "observation": "Revisar JUnit no ecossistema Java.",
            "review_required": "on",
            "last_review": "",
            "next_review": "2026-09-03",
            "review_status": QuestionRecord.ReviewStatus.PENDING,
            "question_url": (
                "https://questoes.grancursosonline.com.br/"
                "questoes-de-concursos/tecnologia-da-informacao-14/4328362"
            ),
            "url_pending": "",
        }
        payload.update(overrides)
        return payload

    def test_question_gets_automatic_display_code(self):
        first = QuestionRecord.objects.create(
            competition_discipline=self.systems_link,
            answered_date=date(2026, 9, 1),
            question_number="Q1",
            result=QuestionRecord.Result.CORRECT,
        )
        second = QuestionRecord.objects.create(
            competition_discipline=self.systems_link,
            answered_date=date(2026, 9, 2),
            question_number="Q2",
            result=QuestionRecord.Result.INCORRECT,
        )

        self.assertEqual(first.code, "Q0001")
        self.assertEqual(second.code, "Q0002")

    def test_question_can_be_linked_to_specific_lesson_and_gran_url(self):
        response = self.client.post(
            reverse(
                "questions:question_create",
                kwargs={
                    "pk": self.competition.pk,
                    "link_id": self.systems_link.pk,
                },
            ),
            self.payload(),
        )

        self.assertEqual(response.status_code, 302)
        question = QuestionRecord.objects.get()
        self.assertEqual(question.competition, self.competition)
        self.assertEqual(question.competition_discipline, self.systems_link)
        self.assertEqual(question.lesson, self.junit)
        self.assertTrue(question.is_gran_url)
        self.assertEqual(question.result, QuestionRecord.Result.INCORRECT)

    def test_board_is_select_with_other_option(self):
        form = QuestionRecordForm(discipline_link=self.systems_link)

        self.assertIn(("FGV", "FGV"), form.fields["board"].choices)
        self.assertIn(("__other__", "Outra banca…"), form.fields["board"].choices)
        self.assertEqual(form.fields["source"].label, "Fonte / origem")
        self.assertEqual(
            form.fields["review_required"].label,
            "Marcar para revisão",
        )

    def test_other_board_value_is_saved(self):
        form = QuestionRecordForm(
            data=self.payload(
                board="__other__",
                board_other="FCC",
            ),
            discipline_link=self.systems_link,
        )

        self.assertTrue(form.is_valid(), form.errors)
        record = form.save()
        self.assertEqual(record.board, "FCC")

    def test_form_only_lists_lessons_from_fixed_discipline(self):
        form = QuestionRecordForm(discipline_link=self.systems_link)

        self.assertEqual(
            list(form.fields["lesson"].queryset),
            [self.junit],
        )
        self.assertNotIn(self.portuguese_lesson, form.fields["lesson"].queryset)

    def test_form_rejects_lesson_from_another_discipline(self):
        form = QuestionRecordForm(
            data=self.payload(lesson=str(self.portuguese_lesson.pk)),
            discipline_link=self.systems_link,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("lesson", form.errors)

    def test_question_url_and_pending_flag_cannot_be_used_together(self):
        form = QuestionRecordForm(
            data=self.payload(url_pending="on"),
            discipline_link=self.systems_link,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("question_url", form.errors)

    def test_question_list_is_compact_and_links_to_detail(self):
        question = QuestionRecord.objects.create(
            competition_discipline=self.systems_link,
            lesson=self.junit,
            answered_date=date(2026, 9, 2),
            board="FGV",
            exam_context="AL-GO — 2026",
            question_number="Slides Q01 — G588",
            topic_subtopic="JUnit",
            user_answer="E",
            answer_key="B",
            result=QuestionRecord.Result.INCORRECT,
            review_required=True,
            review_status=QuestionRecord.ReviewStatus.PENDING,
            next_review=date(2026, 9, 3),
            question_url=(
                "https://questoes.grancursosonline.com.br/"
                "questoes-de-concursos/tecnologia-da-informacao-14/4328362"
            ),
        )
        other = QuestionRecord.objects.create(
            competition_discipline=self.portuguese_link,
            answered_date=date(2026, 9, 3),
            board="FCC",
            question_number="Q02",
            result=QuestionRecord.Result.CORRECT,
        )

        response = self.client.get(
            reverse(
                "questions:question_list",
                kwargs={"pk": self.competition.pk},
            ),
            {
                "disciplina": self.systems_link.pk,
                "resultado": QuestionRecord.Result.INCORRECT,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, question.code)
        self.assertContains(response, "FGV")
        self.assertContains(response, "JUnit")
        self.assertContains(response, self.junit.code)
        self.assertContains(response, "Gran ↗")
        self.assertContains(response, "50")
        self.assertNotContains(response, "AL-GO — 2026")
        self.assertNotContains(response, "03/09/2026")
        self.assertNotContains(response, other.code)
        self.assertEqual(response.context["filtered_total"], 1)
        self.assertEqual(response.context["incorrect_count"], 1)
        self.assertEqual(response.context["accuracy"], 0.0)

        detail_response = self.client.get(
            reverse(
                "questions:question_detail",
                kwargs={
                    "pk": self.competition.pk,
                    "question_id": question.pk,
                },
            )
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Slides Q01 — G588")
        self.assertContains(detail_response, "AL-GO — 2026")
        self.assertContains(detail_response, "03/09/2026")

    def test_lesson_can_preselect_question_form(self):
        response = self.client.get(
            reverse(
                "questions:question_create",
                kwargs={
                    "pk": self.competition.pk,
                    "link_id": self.systems_link.pk,
                },
            ),
            {"aula": self.junit.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].initial["lesson"],
            self.junit.pk,
        )
        self.assertContains(response, "6 - JUnit II")

    def test_question_list_is_paginated(self):
        for number in range(55):
            QuestionRecord.objects.create(
                competition_discipline=self.systems_link,
                answered_date=date(2026, 9, 2),
                question_number=f"Q{number:02d}",
                result=QuestionRecord.Result.CORRECT,
            )

        response = self.client.get(
            reverse(
                "questions:question_list",
                kwargs={"pk": self.competition.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["questions"]), 50)
        self.assertEqual(response.context["page_size"], 50)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)



class GlobalQuestionViewsTests(TestCase):
    def setUp(self):
        board, _ = ExamBoard.objects.get_or_create(
            acronym="FGV",
            defaults={"name": "Fundação Getulio Vargas"},
        )
        other_board, _ = ExamBoard.objects.get_or_create(
            acronym="CESPE",
            defaults={"name": "CESPE"},
        )

        systems = Discipline.objects.create(name="Desenvolvimento de Sistemas")

        self.dataprev = Competition.objects.create(
            name="DATAPREV 2026",
            organization="DATAPREV",
            role="ATI",
            board=board,
            status=Competition.Status.ACTIVE,
        )
        self.other_competition = Competition.objects.create(
            name="Outro Concurso 2027",
            organization="Órgão X",
            role="Analista",
            board=other_board,
            status=Competition.Status.PLANNED,
        )

        self.dataprev_link = CompetitionDiscipline.objects.create(
            competition=self.dataprev,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.other_link = CompetitionDiscipline.objects.create(
            competition=self.other_competition,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )

        QuestionRecord.objects.create(
            competition_discipline=self.dataprev_link,
            answered_date=date(2026, 8, 10),
            board="FGV",
            question_number="Q1",
            result=QuestionRecord.Result.CORRECT,
        )
        QuestionRecord.objects.create(
            competition_discipline=self.dataprev_link,
            answered_date=date(2026, 8, 20),
            board="FGV",
            question_number="Q2",
            result=QuestionRecord.Result.INCORRECT,
        )
        QuestionRecord.objects.create(
            competition_discipline=self.other_link,
            answered_date=date(2027, 1, 15),
            board="CESPE/CEBRASPE",
            question_number="Q3",
            result=QuestionRecord.Result.CORRECT,
        )

    def test_global_question_list_combines_competitions(self):
        response = self.client.get(reverse("questions_global:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DATAPREV 2026")
        self.assertContains(response, "Outro Concurso 2027")
        self.assertContains(response, "Q0001")
        self.assertContains(response, "Q0003")
        self.assertEqual(response.context["page_size"], 50)
        self.assertEqual(response.context["metrics"]["total"], 3)
        self.assertEqual(response.context["metrics"]["correct"], 2)
        self.assertEqual(response.context["metrics"]["incorrect"], 1)
        self.assertEqual(response.context["metrics"]["accuracy"], 66.7)

    def test_global_question_list_filters_by_competition(self):
        response = self.client.get(
            reverse("questions_global:list"),
            {"concurso": self.dataprev.pk},
        )

        self.assertEqual(response.context["metrics"]["total"], 2)
        self.assertContains(response, "Q0001")
        self.assertContains(response, "Q0002")
        self.assertNotContains(response, "Q0003")

    def test_global_dashboard_has_time_and_cross_contest_data(self):
        response = self.client.get(reverse("questions_global:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Questões respondidas ao longo do tempo")
        self.assertContains(response, "Taxa de acerto por concurso")

        chart_data = response.context["chart_data"]
        self.assertEqual(chart_data["months"]["labels"], ["08/2026", "01/2027"])
        self.assertEqual(chart_data["months"]["questions"], [2, 1])
        self.assertEqual(chart_data["months"]["accuracy"], [50.0, 100.0])
        self.assertEqual(response.context["competitions_with_questions"], 2)

    def test_global_new_question_starts_by_choosing_competition(self):
        response = self.client.get(
            reverse("questions_global:choose_competition")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escolha o concurso")
        self.assertContains(response, "DATAPREV 2026")
        self.assertContains(response, "Outro Concurso 2027")



class DataprevQuestionImportTests(TestCase):
    def setUp(self):
        board, _ = ExamBoard.objects.get_or_create(
            acronym="FGV",
            defaults={"name": "Fundação Getulio Vargas"},
        )
        self.competition = Competition.objects.create(
            name="DATAPREV 2026",
            organization="DATAPREV",
            role="ATI — Desenvolvimento de Software",
            board=board,
            status=Competition.Status.ACTIVE,
        )

        discipline_names = [
            "Língua Portuguesa",
            "Língua Inglesa",
            "Raciocínio Lógico Matemático",
            "Atualidades e Inteligência Artificial",
            "Legislação Acerca de Segurança da Informação e Proteção de Dados",
            "Desenvolvimento de Sistemas",
            "Inteligência de Negócios (Business Intelligence)",
            "Segurança da Informação",
            "Banco de Dados",
            "Gestão e Governança de Tecnologia da Informação",
        ]
        for position, name in enumerate(discipline_names, start=1):
            discipline = Discipline.objects.create(name=name)
            CompetitionDiscipline.objects.create(
                competition=self.competition,
                discipline=discipline,
                knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
                priority=CompetitionDiscipline.Priority.P1,
                position=position,
            )

        systems_link = self.competition.discipline_links.get(
            discipline__name="Desenvolvimento de Sistemas"
        )
        Lesson.objects.create(
            competition_discipline=systems_link,
            source_reference="G588",
            title="6 - JUnit II",
        )

    def test_full_snapshot_imports_all_answered_questions(self):
        output = StringIO()
        call_command(
            "import_dataprev_2026_questions",
            competition="DATAPREV 2026",
            stdout=output,
        )

        queryset = QuestionRecord.objects.all()
        self.assertEqual(queryset.count(), 1618)
        self.assertEqual(
            queryset.filter(result=QuestionRecord.Result.CORRECT).count(),
            1191,
        )
        self.assertEqual(
            queryset.filter(result=QuestionRecord.Result.INCORRECT).count(),
            396,
        )
        self.assertEqual(
            queryset.filter(result=QuestionRecord.Result.NOT_COUNTED).count(),
            31,
        )
        self.assertEqual(queryset.exclude(question_url="").count(), 1044)
        self.assertEqual(queryset.filter(url_pending=True).count(), 545)
        self.assertEqual(queryset.filter(review_required=True).count(), 495)
        self.assertEqual(queryset.exclude(code="").count(), 1618)

        linked = queryset.get(
            source_reference="QUESTOES:R1113",
        ) if queryset.filter(source_reference="QUESTOES:R1113").exists() else None
        self.assertIn("Questões no snapshot: 1618", output.getvalue())

    def test_second_import_preserves_existing_records_by_default(self):
        call_command(
            "import_dataprev_2026_questions",
            competition="DATAPREV 2026",
            discipline="Segurança da Informação",
            stdout=StringIO(),
        )
        record = QuestionRecord.objects.first()
        record.observation = "Alteração local posterior."
        record.save(update_fields=["observation"])

        output = StringIO()
        call_command(
            "import_dataprev_2026_questions",
            competition="DATAPREV 2026",
            discipline="Segurança da Informação",
            stdout=output,
        )

        record.refresh_from_db()
        self.assertEqual(record.observation, "Alteração local posterior.")
        self.assertIn("4 preservada(s)", output.getvalue())

    def test_question_import_dry_run_does_not_write(self):
        call_command(
            "import_dataprev_2026_questions",
            competition="DATAPREV 2026",
            discipline="Banco de Dados",
            dry_run=True,
            stdout=StringIO(),
        )

        self.assertFalse(QuestionRecord.objects.exists())

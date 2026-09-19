from datetime import date

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

    def test_question_list_shows_gran_link_and_filters(self):
        QuestionRecord.objects.create(
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
            question_url=(
                "https://questoes.grancursosonline.com.br/"
                "questoes-de-concursos/tecnologia-da-informacao-14/4328362"
            ),
        )
        QuestionRecord.objects.create(
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
        self.assertContains(response, "Slides Q01 — G588")
        self.assertContains(response, "Gran ↗")
        self.assertNotContains(response, "Q02")
        self.assertEqual(response.context["filtered_total"], 1)
        self.assertEqual(response.context["incorrect_count"], 1)
        self.assertEqual(response.context["accuracy"], 0.0)

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
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

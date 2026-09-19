from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.competitions.models import (
    Competition,
    CompetitionDiscipline,
    Discipline,
    ExamBoard,
    SyllabusItem,
)

from .forms import LessonForm
from .models import Lesson


class LessonTests(TestCase):
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
        database = Discipline.objects.create(name="Banco de Dados")
        self.systems_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.database_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=database,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.systems_item = SyllabusItem.objects.create(
            competition_discipline=self.systems_link,
            content="Testes de software.",
        )
        self.database_item = SyllabusItem.objects.create(
            competition_discipline=self.database_link,
            content="Modelagem de dados.",
        )

    def test_lesson_position_and_accuracy(self):
        lesson = Lesson.objects.create(
            competition_discipline=self.systems_link,
            code="G588",
            title="JUnit",
            questions_done=10,
            correct_answers=8,
        )

        self.assertEqual(lesson.position, 1)
        self.assertEqual(lesson.accuracy, 80)

    def test_lesson_can_be_created_and_linked_to_syllabus(self):
        response = self.client.post(
            reverse("studies:lesson_create", kwargs={"pk": self.competition.pk}),
            {
                "competition_discipline": self.systems_link.pk,
                "code": "G588",
                "title": "JUnit",
                "macrotheme": "Testes de software",
                "syllabus_items": [self.systems_item.pk],
                "source": "Gran Cursos Online",
                "suggested_week": "12",
                "planned_date": "2026-09-20",
                "studied_date": "",
                "status": Lesson.Status.IN_PROGRESS,
                "video_url": "https://example.com/video",
                "transcript_url": "https://example.com/transcript",
                "handout_url": "https://example.com/handout",
                "questions_done": "5",
                "correct_answers": "4",
                "notes": "Continuar pela próxima degravação.",
            },
        )

        self.assertEqual(response.status_code, 302)
        lesson = Lesson.objects.get(code="G588")
        self.assertEqual(lesson.competition_discipline, self.systems_link)
        self.assertEqual(lesson.suggested_week, 12)
        self.assertEqual(lesson.planned_date, date(2026, 9, 20))
        self.assertEqual(list(lesson.syllabus_items.all()), [self.systems_item])

    def test_form_rejects_syllabus_item_from_another_discipline(self):
        form = LessonForm(
            data={
                "competition_discipline": self.systems_link.pk,
                "code": "G589",
                "title": "JUnit II",
                "macrotheme": "Testes de software",
                "syllabus_items": [self.database_item.pk],
                "source": "Gran Cursos Online",
                "suggested_week": "",
                "planned_date": "",
                "studied_date": "",
                "status": Lesson.Status.NOT_STARTED,
                "video_url": "",
                "transcript_url": "",
                "handout_url": "",
                "questions_done": "",
                "correct_answers": "",
                "notes": "",
            },
            competition=self.competition,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("syllabus_items", form.errors)

    def test_form_rejects_more_correct_answers_than_questions(self):
        form = LessonForm(
            data={
                "competition_discipline": self.systems_link.pk,
                "code": "G590",
                "title": "JUnit III",
                "macrotheme": "",
                "syllabus_items": [],
                "source": "Gran Cursos Online",
                "suggested_week": "",
                "planned_date": "",
                "studied_date": "",
                "status": Lesson.Status.NOT_STARTED,
                "video_url": "",
                "transcript_url": "",
                "handout_url": "",
                "questions_done": "3",
                "correct_answers": "4",
                "notes": "",
            },
            competition=self.competition,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("correct_answers", form.errors)

    def test_lesson_list_filters_by_discipline_week_status_and_search(self):
        Lesson.objects.create(
            competition_discipline=self.systems_link,
            code="G588",
            title="JUnit",
            suggested_week=12,
            status=Lesson.Status.IN_PROGRESS,
        )
        Lesson.objects.create(
            competition_discipline=self.database_link,
            code="G700",
            title="Normalização",
            suggested_week=13,
            status=Lesson.Status.NOT_STARTED,
        )

        response = self.client.get(
            reverse("studies:lesson_list", kwargs={"pk": self.competition.pk}),
            {
                "disciplina": self.systems_link.pk,
                "semana": "12",
                "status": Lesson.Status.IN_PROGRESS,
                "q": "JUnit",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "G588")
        self.assertNotContains(response, "G700")
        self.assertEqual(response.context["filtered_total"], 1)

    def test_lesson_can_be_edited(self):
        lesson = Lesson.objects.create(
            competition_discipline=self.systems_link,
            code="G588",
            title="JUnit",
            status=Lesson.Status.NOT_STARTED,
        )

        response = self.client.post(
            reverse(
                "studies:lesson_edit",
                kwargs={"pk": self.competition.pk, "lesson_id": lesson.pk},
            ),
            {
                "competition_discipline": self.systems_link.pk,
                "code": "G588",
                "title": "JUnit — testes unitários",
                "macrotheme": "Testes",
                "syllabus_items": [self.systems_item.pk],
                "source": "Gran Cursos Online",
                "suggested_week": "12",
                "planned_date": "",
                "studied_date": "2026-09-19",
                "status": Lesson.Status.COMPLETED,
                "video_url": "",
                "transcript_url": "",
                "handout_url": "",
                "questions_done": "5",
                "correct_answers": "5",
                "notes": "Concluída.",
            },
        )

        self.assertEqual(response.status_code, 302)
        lesson.refresh_from_db()
        self.assertEqual(lesson.status, Lesson.Status.COMPLETED)
        self.assertEqual(lesson.studied_date, date(2026, 9, 19))
        self.assertEqual(lesson.correct_answers, 5)

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
        self.systems_item_2 = SyllabusItem.objects.create(
            competition_discipline=self.systems_link,
            content="Testes automatizados.",
        )
        self.database_item = SyllabusItem.objects.create(
            competition_discipline=self.database_link,
            content="Modelagem de dados.",
        )

    def lesson_payload(self, **overrides):
        payload = {
            "title": "JUnit",
            "macrotheme": "Testes de software — JUnit",
            "syllabus_items": [self.systems_item.pk],
            "source": "Gran Cursos Online",
            "suggested_week": "7",
            "planned_date": "2026-09-29",
            "studied_date": "",
            "status": Lesson.Status.IN_PROGRESS,
            "video_url": "https://example.com/video",
            "transcript_url": "",
            "handout_url": "",
            "questions_done": "5",
            "correct_answers": "4",
            "notes": "Continuar pela próxima aula.",
        }
        payload.update(overrides)
        return payload

    def test_lesson_code_is_generated_automatically(self):
        first = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit II",
        )
        second = Lesson.objects.create(
            competition_discipline=self.database_link,
            title="Normalização",
        )

        self.assertEqual(first.code, "G0001")
        self.assertEqual(second.code, "G0002")

    def test_lesson_position_and_accuracy(self):
        lesson = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            questions_done=10,
            correct_answers=8,
        )

        self.assertEqual(lesson.position, 1)
        self.assertEqual(lesson.accuracy, 80)

    def test_form_does_not_expose_discipline_or_code(self):
        form = LessonForm(discipline_link=self.systems_link)

        self.assertNotIn("competition_discipline", form.fields)
        self.assertNotIn("code", form.fields)
        self.assertEqual(
            list(form.fields["syllabus_items"].queryset),
            [self.systems_item, self.systems_item_2],
        )

    def test_lesson_can_be_created_and_linked_to_multiple_syllabus_items(self):
        response = self.client.post(
            reverse(
                "studies:lesson_create",
                kwargs={
                    "pk": self.competition.pk,
                    "link_id": self.systems_link.pk,
                },
            ),
            self.lesson_payload(
                syllabus_items=[
                    self.systems_item.pk,
                    self.systems_item_2.pk,
                ]
            ),
        )

        self.assertEqual(response.status_code, 302)
        lesson = Lesson.objects.get()
        self.assertEqual(lesson.code, "G0001")
        self.assertEqual(lesson.competition_discipline, self.systems_link)
        self.assertEqual(lesson.suggested_week, 7)
        self.assertEqual(lesson.planned_date, date(2026, 9, 29))
        self.assertEqual(
            list(lesson.syllabus_items.order_by("position")),
            [self.systems_item, self.systems_item_2],
        )

    def test_form_only_accepts_syllabus_items_from_fixed_discipline(self):
        form = LessonForm(
            data=self.lesson_payload(
                syllabus_items=[self.database_item.pk]
            ),
            discipline_link=self.systems_link,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("syllabus_items", form.errors)

    def test_form_rejects_more_correct_answers_than_questions(self):
        form = LessonForm(
            data=self.lesson_payload(
                questions_done="3",
                correct_answers="4",
            ),
            discipline_link=self.systems_link,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("correct_answers", form.errors)

    def test_global_add_lesson_first_shows_discipline_chooser(self):
        response = self.client.get(
            reverse(
                "studies:lesson_choose_discipline",
                kwargs={"pk": self.competition.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escolha a disciplina")
        self.assertContains(response, "Desenvolvimento de Sistemas")
        self.assertContains(response, "Banco de Dados")

    def test_lesson_form_displays_fixed_discipline_as_text(self):
        response = self.client.get(
            reverse(
                "studies:lesson_create",
                kwargs={
                    "pk": self.competition.pk,
                    "link_id": self.systems_link.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desenvolvimento de Sistemas")
        self.assertContains(response, "Gerado automaticamente ao salvar")
        self.assertNotContains(response, 'name="competition_discipline"')
        self.assertNotContains(response, 'name="code"')
        self.assertNotContains(response, "Modelagem de dados.")

    def test_lesson_list_filters_by_discipline_week_status_and_search(self):
        first = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            macrotheme="Testes de software — JUnit",
            suggested_week=12,
            status=Lesson.Status.IN_PROGRESS,
        )
        second = Lesson.objects.create(
            competition_discipline=self.database_link,
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
        self.assertContains(response, first.code)
        self.assertNotContains(response, second.code)
        self.assertEqual(response.context["filtered_total"], 1)

    def test_lesson_list_has_separate_question_accuracy_columns(self):
        Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            questions_done=17,
            correct_answers=13,
        )

        response = self.client.get(
            reverse("studies:lesson_list", kwargs={"pk": self.competition.pk})
        )

        self.assertContains(response, "<th>Questões</th>", html=True)
        self.assertContains(response, "<th>Acertos</th>", html=True)
        self.assertContains(response, "<th>%</th>", html=True)
        self.assertNotContains(response, "Edital:")

    def test_lesson_actions_show_material_links_and_edit(self):
        lesson = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            video_url="https://example.com/video",
            transcript_url="https://example.com/transcript",
            handout_url="",
        )

        response = self.client.get(
            reverse("studies:lesson_list", kwargs={"pk": self.competition.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ações")
        self.assertContains(response, 'popover="auto"')
        self.assertContains(response, 'data-lesson-popover')
        self.assertContains(response, "Videoaula ↗")
        self.assertContains(response, "Degravação ↗")
        self.assertContains(response, "Apostila —")
        self.assertContains(response, "Editar aula")
        self.assertContains(response, 'href="https://example.com/video"')
        self.assertContains(response, 'href="https://example.com/transcript"')

    def test_lesson_can_be_edited_without_changing_discipline_or_code(self):
        lesson = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            status=Lesson.Status.NOT_STARTED,
        )
        original_code = lesson.code

        response = self.client.post(
            reverse(
                "studies:lesson_edit",
                kwargs={"pk": self.competition.pk, "lesson_id": lesson.pk},
            ),
            self.lesson_payload(
                title="JUnit — testes unitários",
                studied_date="2026-09-19",
                status=Lesson.Status.COMPLETED,
                questions_done="5",
                correct_answers="5",
                notes="Concluída.",
            ),
        )

        self.assertEqual(response.status_code, 302)
        lesson.refresh_from_db()
        self.assertEqual(lesson.code, original_code)
        self.assertEqual(lesson.competition_discipline, self.systems_link)
        self.assertEqual(lesson.status, Lesson.Status.COMPLETED)
        self.assertEqual(lesson.studied_date, date(2026, 9, 19))
        self.assertEqual(lesson.correct_answers, 5)



class DataprevLessonImportTests(TestCase):
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
        discipline = Discipline.objects.create(
            name="Inteligência de Negócios (Business Intelligence)"
        )
        self.link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )
        for code in ["1", "2", "3", "4", "5", "6", "7"]:
            SyllabusItem.objects.create(
                competition_discipline=self.link,
                item_code=code,
                content=f"Conteúdo BI {code}",
            )

    def test_import_can_adopt_manual_lesson_and_create_remaining_rows(self):
        manual = Lesson.objects.create(
            competition_discipline=self.link,
            title="1 - Business Intelligence - Introdução",
        )
        original_code = manual.code

        output = StringIO()
        call_command(
            "import_dataprev_2026_lessons",
            competition="DATAPREV 2026",
            discipline="Inteligência de Negócios (Business Intelligence)",
            stdout=output,
        )

        self.assertEqual(Lesson.objects.count(), 17)

        manual.refresh_from_db()
        self.assertEqual(manual.code, original_code)
        self.assertEqual(manual.source_reference, "G764")
        self.assertEqual(manual.position, 1)
        self.assertEqual(manual.status, Lesson.Status.IN_PROGRESS)
        self.assertTrue(manual.video_url.startswith("https://www.grancursosonline.com.br/"))
        self.assertTrue(manual.transcript_url.startswith("https://drive.google.com/"))
        self.assertTrue(manual.handout_url.startswith("https://drive.google.com/"))
        self.assertEqual(
            list(manual.syllabus_items.values_list("item_code", flat=True)),
            ["1"],
        )
        self.assertIn("16 criada(s)", output.getvalue())
        self.assertIn("1 cadastro(s) manual(is) aproveitado(s)", output.getvalue())

    def test_second_import_preserves_existing_imported_lessons_by_default(self):
        call_command(
            "import_dataprev_2026_lessons",
            competition="DATAPREV 2026",
            discipline="Inteligência de Negócios (Business Intelligence)",
            stdout=StringIO(),
        )
        lesson = Lesson.objects.get(source_reference="G764")
        lesson.notes = "Anotação local posterior à importação."
        lesson.save(update_fields=["notes"])

        output = StringIO()
        call_command(
            "import_dataprev_2026_lessons",
            competition="DATAPREV 2026",
            discipline="Inteligência de Negócios (Business Intelligence)",
            stdout=output,
        )

        lesson.refresh_from_db()
        self.assertEqual(lesson.notes, "Anotação local posterior à importação.")
        self.assertIn("17 preservada(s)", output.getvalue())

    def test_dry_run_does_not_create_lessons(self):
        call_command(
            "import_dataprev_2026_lessons",
            competition="DATAPREV 2026",
            discipline="Inteligência de Negócios (Business Intelligence)",
            dry_run=True,
            stdout=StringIO(),
        )

        self.assertFalse(Lesson.objects.exists())



class CompetitionDashboardTests(TestCase):
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
            exam_date=date(2026, 10, 11),
        )

        portuguese = Discipline.objects.create(name="Língua Portuguesa")
        systems = Discipline.objects.create(name="Desenvolvimento de Sistemas")

        self.portuguese_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=portuguese,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.GENERAL,
            priority=CompetitionDiscipline.Priority.P1,
        )
        self.systems_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )

        self.pt_item = SyllabusItem.objects.create(
            competition_discipline=self.portuguese_link,
            content="Classes de palavras.",
        )
        self.dev_item_1 = SyllabusItem.objects.create(
            competition_discipline=self.systems_link,
            content="Testes de software.",
        )
        self.dev_item_2 = SyllabusItem.objects.create(
            competition_discipline=self.systems_link,
            content="DevOps.",
        )

        completed = Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="JUnit",
            status=Lesson.Status.COMPLETED,
            questions_done=10,
            correct_answers=8,
            suggested_week=1,
        )
        completed.syllabus_items.add(self.dev_item_1)

        Lesson.objects.create(
            competition_discipline=self.systems_link,
            title="DevOps",
            status=Lesson.Status.IN_PROGRESS,
            questions_done=5,
            correct_answers=3,
            suggested_week=1,
        )

        Lesson.objects.create(
            competition_discipline=self.portuguese_link,
            title="Classes de Palavras",
            status=Lesson.Status.NOT_STARTED,
            suggested_week=2,
        )

    def test_dashboard_uses_real_lesson_question_and_syllabus_data(self):
        response = self.client.get(
            reverse(
                "competitions:dashboard",
                kwargs={"pk": self.competition.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_lessons"], 3)
        self.assertEqual(response.context["completed_lessons"], 1)
        self.assertEqual(response.context["in_progress_lessons"], 1)
        self.assertEqual(response.context["not_started_lessons"], 1)
        self.assertEqual(response.context["lesson_progress"], 33.3)
        self.assertEqual(response.context["total_questions"], 15)
        self.assertEqual(response.context["total_correct"], 11)
        self.assertEqual(response.context["overall_accuracy"], 73.3)
        self.assertEqual(response.context["total_syllabus_items"], 3)
        self.assertEqual(response.context["covered_syllabus_items"], 1)
        self.assertEqual(response.context["syllabus_coverage"], 33.3)

        chart_data = response.context["chart_data"]
        self.assertEqual(
            chart_data["status"]["values"],
            [1, 1, 1],
        )
        self.assertEqual(
            chart_data["weeks"]["labels"],
            ["Semana 1", "Semana 2"],
        )

        self.assertContains(response, "Progresso por disciplina")
        self.assertContains(response, "Taxa de acerto por disciplina")
        self.assertContains(response, "Aulas por semana sugerida")
        self.assertContains(response, "competition-dashboard-data")

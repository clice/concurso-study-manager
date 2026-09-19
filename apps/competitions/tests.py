from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Competition, CompetitionDiscipline, CompetitionStage, Discipline


class CompetitionRegistrationTests(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            name="DATAPREV 2026",
            organization="DATAPREV",
            role="ATI — Desenvolvimento de Software",
            board="FGV",
            exam_date=date(2026, 10, 11),
            status=Competition.Status.ACTIVE,
        )

    def test_create_page_loads(self):
        response = self.client.get(reverse("competitions:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Novo concurso")

    def test_competition_can_be_created(self):
        response = self.client.post(
            reverse("competitions:create"),
            {
                "name": "Concurso Exemplo",
                "organization": "Órgão Exemplo",
                "role": "Analista",
                "notice_number": "01/2026",
                "board": "FGV",
                "initial_salary": "10000.00",
                "benefits": "Benefício exemplo",
                "fee": "100.00",
                "registration_start": "",
                "registration_end": "",
                "exam_date": "2026-12-01",
                "exam_time": "13:00",
                "validity": "2 anos",
                "location": "Ceará",
                "official_url": "https://example.com/",
                "status": Competition.Status.PLANNED,
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Competition.objects.filter(name="Concurso Exemplo").exists())

    def test_stage_can_be_added(self):
        response = self.client.post(
            reverse("competitions:stage_add", kwargs={"pk": self.competition.pk}),
            {
                "name": "Prova objetiva",
                "stage_type": CompetitionStage.StageType.OBJECTIVE,
                "position": 1,
                "scheduled_date": "2026-10-11",
                "scheduled_time": "13:00",
                "eliminatory": "on",
                "classificatory": "on",
                "max_score": "115.00",
                "minimum_score": "57.50",
                "details": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.competition.stages.count(), 1)

    def test_existing_discipline_is_reused_between_competitions(self):
        stage = CompetitionStage.objects.create(
            competition=self.competition,
            name="Prova objetiva",
            stage_type=CompetitionStage.StageType.OBJECTIVE,
            position=1,
        )
        Discipline.objects.create(name="Língua Portuguesa")

        response = self.client.post(
            reverse("competitions:discipline_add", kwargs={"pk": self.competition.pk}),
            {
                "stage": stage.pk,
                "discipline_name": "língua portuguesa",
                "knowledge_area": CompetitionDiscipline.KnowledgeArea.GENERAL,
                "priority": CompetitionDiscipline.Priority.P1,
                "expected_questions": 12,
                "weight": "1.00",
                "max_score": "12.00",
                "position": 1,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Discipline.objects.count(), 1)
        link = CompetitionDiscipline.objects.get()
        self.assertEqual(link.discipline.name, "Língua Portuguesa")
        self.assertEqual(link.competition, self.competition)
        self.assertEqual(link.stage, stage)

    def test_detail_page_displays_stages_and_disciplines(self):
        stage = CompetitionStage.objects.create(
            competition=self.competition,
            name="Prova objetiva",
            stage_type=CompetitionStage.StageType.OBJECTIVE,
            position=1,
        )
        discipline = Discipline.objects.create(name="Banco de Dados")
        CompetitionDiscipline.objects.create(
            competition=self.competition,
            stage=stage,
            discipline=discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
            expected_questions=3,
            weight=2.5,
            max_score=7.5,
            position=1,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prova objetiva")
        self.assertContains(response, "Banco de Dados")

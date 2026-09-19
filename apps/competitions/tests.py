from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import (
    Competition,
    CompetitionDiscipline,
    CompetitionStage,
    Discipline,
    ExamBoard,
)


class CompetitionRegistrationTests(TestCase):
    def setUp(self):
        self.fgv, _ = ExamBoard.objects.get_or_create(
            acronym="FGV",
            defaults={"name": "Fundação Getulio Vargas"},
        )
        self.competition = Competition.objects.create(
            name="DATAPREV 2026",
            organization="DATAPREV",
            role="ATI — Desenvolvimento de Software",
            board=self.fgv,
            exam_date=date(2026, 10, 11),
            status=Competition.Status.ACTIVE,
        )

    def test_create_page_loads_with_board_select(self):
        response = self.client.get(reverse("competitions:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Novo concurso")
        self.assertContains(response, "FGV")

    def test_competition_can_be_created_with_brazilian_currency(self):
        response = self.client.post(
            reverse("competitions:create"),
            {
                "name": "Concurso Exemplo",
                "organization": "Órgão Exemplo",
                "role": "Analista",
                "board": self.fgv.pk,
                "initial_salary": "R$ 10.685,44",
                "benefits": "Benefício exemplo",
                "fee": "R$ 110,00",
                "registration_start": "2026-07-06",
                "registration_end": "2026-08-06",
                "exam_date": "2026-12-01",
                "exam_time": "13:00",
                "location": "Ceará",
                "official_url": "https://example.com/",
                "status": Competition.Status.PLANNED,
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        competition = Competition.objects.get(name="Concurso Exemplo")
        self.assertEqual(competition.initial_salary, Decimal("10685.44"))
        self.assertEqual(competition.fee, Decimal("110.00"))
        self.assertEqual(competition.registration_start, date(2026, 7, 6))
        self.assertEqual(competition.registration_end, date(2026, 8, 6))
        self.assertEqual(competition.board, self.fgv)

    def test_stages_receive_positions_automatically(self):
        first = CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.OBJECTIVE,
        )
        second = CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.ESSAY,
        )

        self.assertEqual(first.position, 1)
        self.assertEqual(second.position, 2)

    def test_stage_can_be_added_without_name_or_manual_position(self):
        response = self.client.post(
            reverse("competitions:stage_add", kwargs={"pk": self.competition.pk}),
            {
                "stage_type": CompetitionStage.StageType.OBJECTIVE,
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

        stage = self.competition.stages.get()
        self.assertEqual(stage.position, 1)
        self.assertEqual(stage.get_stage_type_display(), "Prova objetiva")

    def test_heteroidentification_and_biopsychosocial_are_available_stage_types(self):
        available = dict(CompetitionStage.StageType.choices)
        self.assertEqual(
            available[CompetitionStage.StageType.HETEROIDENTIFICATION],
            "Heteroidentificação",
        )
        self.assertEqual(
            available[CompetitionStage.StageType.BIOPSYCHOSOCIAL],
            "Avaliação biopsicossocial",
        )

    def test_existing_discipline_is_reused_between_competitions(self):
        Discipline.objects.create(name="Língua Portuguesa")

        response = self.client.post(
            reverse("competitions:discipline_add", kwargs={"pk": self.competition.pk}),
            {
                "discipline_name": "língua portuguesa",
                "knowledge_area": CompetitionDiscipline.KnowledgeArea.GENERAL,
                "priority": CompetitionDiscipline.Priority.P1,
                "expected_questions": 12,
                "weight": "1.00",
                "max_score": "12.00",
                "minimum_score": "1.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Discipline.objects.count(), 1)

        link = CompetitionDiscipline.objects.get()
        self.assertEqual(link.discipline.name, "Língua Portuguesa")
        self.assertEqual(link.competition, self.competition)
        self.assertEqual(link.position, 1)
        self.assertEqual(link.minimum_score, Decimal("1.00"))

    def test_detail_page_displays_stages_and_disciplines(self):
        CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.OBJECTIVE,
        )
        discipline = Discipline.objects.create(name="Banco de Dados")
        CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
            weight=2.5,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prova objetiva")
        self.assertContains(response, "Banco de Dados")
        self.assertContains(response, "FGV")
        self.assertNotContains(response, "<th>Etapa</th>", html=False)
        self.assertNotContains(response, "<th>Posição</th>", html=False)

    def test_stage_order_can_be_rearranged(self):
        objective = CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.OBJECTIVE,
        )
        essay = CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.ESSAY,
        )

        response = self.client.post(
            reverse("competitions:stage_reorder", kwargs={"pk": self.competition.pk}),
            data=f'{{"order":[{essay.id},{objective.id}]}}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        objective.refresh_from_db()
        essay.refresh_from_db()
        self.assertEqual(essay.position, 1)
        self.assertEqual(objective.position, 2)

    def test_discipline_order_can_be_rearranged(self):
        portuguese = Discipline.objects.create(name="Língua Portuguesa")
        english = Discipline.objects.create(name="Língua Inglesa")
        first = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=portuguese,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.GENERAL,
        )
        second = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=english,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.GENERAL,
        )

        response = self.client.post(
            reverse("competitions:discipline_reorder", kwargs={"pk": self.competition.pk}),
            data=f'{{"order":[{second.id},{first.id}]}}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(second.position, 1)
        self.assertEqual(first.position, 2)

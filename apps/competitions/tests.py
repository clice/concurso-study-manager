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
    SyllabusItem,
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
                "question_count_kind": CompetitionDiscipline.QuestionCountKind.OFFICIAL,
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


    def test_stage_can_be_edited_with_nonzero_rule(self):
        stage = CompetitionStage.objects.create(
            competition=self.competition,
            stage_type=CompetitionStage.StageType.OBJECTIVE,
        )

        response = self.client.post(
            reverse(
                "competitions:stage_edit",
                kwargs={"pk": self.competition.pk, "stage_id": stage.pk},
            ),
            {
                "stage_type": CompetitionStage.StageType.OBJECTIVE,
                "scheduled_date": "2026-10-11",
                "scheduled_time": "13:00",
                "max_score": "115.00",
                "minimum_score": "57.50",
                "eliminatory": "on",
                "classificatory": "on",
                "requires_nonzero_each_discipline": "on",
                "details": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        stage.refresh_from_db()
        self.assertEqual(stage.minimum_score, Decimal("57.50"))
        self.assertTrue(stage.requires_nonzero_each_discipline)

    def test_discipline_can_be_edited_as_estimated(self):
        discipline = Discipline.objects.create(name="Desenvolvimento de Sistemas")
        link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )

        response = self.client.post(
            reverse(
                "competitions:discipline_edit",
                kwargs={"pk": self.competition.pk, "link_id": link.pk},
            ),
            {
                "discipline_name": "Desenvolvimento de Sistemas",
                "knowledge_area": CompetitionDiscipline.KnowledgeArea.SPECIFIC,
                "priority": CompetitionDiscipline.Priority.P1,
                "expected_questions": "18",
                "question_count_kind": CompetitionDiscipline.QuestionCountKind.ESTIMATED,
                "weight": "2.50",
                "max_score": "45.00",
                "minimum_score": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertEqual(link.expected_questions, 18)
        self.assertEqual(
            link.question_count_kind,
            CompetitionDiscipline.QuestionCountKind.ESTIMATED,
        )

    def test_detail_displays_totals_and_estimate_warning(self):
        portuguese = Discipline.objects.create(name="Língua Portuguesa")
        systems = Discipline.objects.create(name="Desenvolvimento de Sistemas")
        CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=portuguese,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.GENERAL,
            expected_questions=12,
            question_count_kind=CompetitionDiscipline.QuestionCountKind.OFFICIAL,
            weight=1,
            max_score=12,
        )
        CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=systems,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            expected_questions=18,
            question_count_kind=CompetitionDiscipline.QuestionCountKind.ESTIMATED,
            weight=2.5,
            max_score=45,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk})
        )

        self.assertContains(response, "indica que o número de questões é uma estimativa")
        self.assertContains(response, 'aria-label="Estimativa"', count=1)
        self.assertContains(response, 'aria-label="O total inclui estimativas"', count=1)
        self.assertEqual(response.context["total_questions"], 30)
        self.assertEqual(response.context["total_max_score"], Decimal("57"))


    def test_unicode_casefold_reuses_existing_discipline(self):
        Discipline.objects.create(name="LÍNGUA PORTUGUESA")

        response = self.client.post(
            reverse("competitions:discipline_add", kwargs={"pk": self.competition.pk}),
            {
                "discipline_name": "Língua Portuguesa",
                "knowledge_area": CompetitionDiscipline.KnowledgeArea.GENERAL,
                "priority": CompetitionDiscipline.Priority.P1,
                "expected_questions": "12",
                "question_count_kind": CompetitionDiscipline.QuestionCountKind.OFFICIAL,
                "weight": "1.00",
                "max_score": "12.00",
                "minimum_score": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Discipline.objects.count(), 1)




class SyllabusItemTests(TestCase):
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
        discipline = Discipline.objects.create(name="Desenvolvimento de Sistemas")
        self.link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
            priority=CompetitionDiscipline.Priority.P1,
        )

    def test_syllabus_items_receive_positions_automatically(self):
        first = SyllabusItem.objects.create(
            competition_discipline=self.link,
            item_code="1",
            content="Engenharia de software",
        )
        second = SyllabusItem.objects.create(
            competition_discipline=self.link,
            item_code="2",
            content="Testes de software",
        )

        self.assertEqual(first.position, 1)
        self.assertEqual(second.position, 2)

    def test_syllabus_item_form_only_exposes_parent_and_content(self):
        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk}),
            {"edital": self.link.pk},
        )

        block = response.context["syllabus_blocks"][0]
        self.assertEqual(list(block["form"].fields), ["parent", "content"])

    def test_syllabus_item_can_be_added_with_automatic_code(self):
        response = self.client.post(
            reverse(
                "competitions:syllabus_item_add",
                kwargs={"pk": self.competition.pk, "link_id": self.link.pk},
            ),
            {
                f"syllabus-{self.link.pk}-parent": "",
                f"syllabus-{self.link.pk}-content": "Testes unitários",
            },
        )

        self.assertEqual(response.status_code, 302)
        item = SyllabusItem.objects.get()
        self.assertEqual(item.item_code, "1")
        self.assertEqual(item.content, "Testes unitários")
        self.assertEqual(item.competition_discipline, self.link)

    def test_syllabus_parent_must_belong_to_same_discipline(self):
        other_discipline = Discipline.objects.create(name="Banco de Dados")
        other_link = CompetitionDiscipline.objects.create(
            competition=self.competition,
            discipline=other_discipline,
            knowledge_area=CompetitionDiscipline.KnowledgeArea.SPECIFIC,
        )
        foreign_parent = SyllabusItem.objects.create(
            competition_discipline=other_link,
            content="Modelo relacional",
        )

        response = self.client.post(
            reverse(
                "competitions:syllabus_item_add",
                kwargs={"pk": self.competition.pk, "link_id": self.link.pk},
            ),
            {
                f"syllabus-{self.link.pk}-parent": str(foreign_parent.pk),
                f"syllabus-{self.link.pk}-content": "Subitem inválido",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SyllabusItem.objects.filter(competition_discipline=self.link).count(),
            0,
        )

    def test_syllabus_item_can_be_edited(self):
        item = SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Conteúdo inicial",
        )

        response = self.client.post(
            reverse(
                "competitions:syllabus_item_edit",
                kwargs={"pk": self.competition.pk, "item_id": item.pk},
            ),
            {
                "parent": "",
                "content": "Conteúdo atualizado",
            },
        )

        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.content, "Conteúdo atualizado")

    def test_syllabus_items_can_be_reordered(self):
        first = SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Primeiro",
        )
        second = SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Segundo",
        )

        response = self.client.post(
            reverse(
                "competitions:syllabus_item_reorder",
                kwargs={"pk": self.competition.pk, "link_id": self.link.pk},
            ),
            data=f'{{"order":[{second.id},{first.id}]}}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(second.position, 1)
        self.assertEqual(first.position, 2)

    def test_competition_detail_groups_syllabus_by_discipline(self):
        parent = SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Testes de software",
        )
        SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Testes unitários",
            parent=parent,
        )

        response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edital verticalizado")
        self.assertContains(response, "Desenvolvimento de Sistemas")
        self.assertContains(response, "1.1")
        self.assertContains(response, "subitem de 1")
        self.assertContains(response, "Conhecimentos Específicos · P1")
        self.assertEqual(response.context["total_syllabus_items"], 2)
        self.assertEqual(response.context["syllabus_discipline_count"], 1)

    def test_syllabus_code_is_generated_from_hierarchy(self):
        root = SyllabusItem.objects.create(
            competition_discipline=self.link,
            content="Engenharia de software",
        )
        child = SyllabusItem.objects.create(
            competition_discipline=self.link,
            parent=root,
            content="Requisitos de software",
        )
        second_child = SyllabusItem.objects.create(
            competition_discipline=self.link,
            parent=root,
            content="Projeto de software",
        )

        self.assertEqual(root.item_code, "1")
        self.assertEqual(child.item_code, "1.1")
        self.assertEqual(second_child.item_code, "1.2")

    def test_saving_item_redirects_to_open_same_discipline(self):
        response = self.client.post(
            reverse(
                "competitions:syllabus_item_add",
                kwargs={"pk": self.competition.pk, "link_id": self.link.pk},
            ),
            {
                f"syllabus-{self.link.pk}-parent": "",
                f"syllabus-{self.link.pk}-content": "Engenharia de software",
            },
        )

        expected = (
            reverse("competitions:detail", kwargs={"pk": self.competition.pk})
            + f"?edital={self.link.pk}#edital-{self.link.pk}"
        )
        self.assertRedirects(response, expected, fetch_redirect_response=False)

        detail_response = self.client.get(
            reverse("competitions:detail", kwargs={"pk": self.competition.pk}),
            {"edital": self.link.pk},
        )
        self.assertEqual(detail_response.context["open_syllabus_link_id"], self.link.pk)

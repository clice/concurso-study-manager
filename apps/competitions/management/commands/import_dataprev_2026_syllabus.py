from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.competitions.models import Competition, SyllabusItem, normalize_discipline_name


SYLLABUS = [
    {
        "aliases": ["Atualidades e Inteligência Artificial"],
        "items": [
            (
                "1",
                None,
                "Tópicos relevantes e atuais de diversas áreas, tais como segurança, transportes, política, economia, sociedade, educação, saúde, cultura, tecnologia, energia, relações internacionais, desenvolvimento sustentável e ecologia.",
            ),
            (
                "2",
                None,
                "Inteligência Artificial: fundamentos e aplicações: conceitos de inteligência artificial; aprendizado da máquina; introdução aos modelos generativos e modelos de linguagem; ética, governança e privacidade em IA.",
            ),
        ],
    },
    {
        "aliases": [
            "Legislação Acerca de Segurança da Informação e Proteção de Dados",
            "Legislação acerca de Segurança da Informação e Proteção de Dados",
        ],
        "items": [
            (
                "1",
                None,
                "Lei nº 12.527/2011 (Lei de Acesso à Informação): capítulos I, II, III, IV e V; Dec. nº 7.724 e nº 7845.",
            ),
            (
                "2",
                None,
                "Lei nº 12.737/2012 (Lei de Delitos Informáticos): art. 2º.",
            ),
            (
                "3",
                None,
                "Lei nº 12.965/2014 (Marco Civil da Internet): capítulos II, Seção I, e III, Seções I e II.",
            ),
            (
                "4",
                None,
                "Lei nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais – LGPD): capítulos I, II, III, IV, VII, VIII e IX.",
            ),
        ],
    },
    {
        "aliases": ["Desenvolvimento de Sistemas"],
        "items": [
            (
                "1",
                None,
                "Desenvolvimento de sistemas. Desenvolvimento em Linguagens de programação Java (versão 6 ou superior), JavaEE (versão 6 ou superior), JakartaEE, JPA (versão 2 ou superior), Javascript, frameworks JUnit, Hibernate, JSF, Primefaces, Spring, SpringCloud e SpringBoot. Desenvolvimento para dispositivos móveis (Android e iOs). Desenvolvimento em ferramentas low-code e no-code.",
            ),
            (
                "2",
                None,
                "Análise estática de código-fonte (clean code e ferramenta SonarQube).",
            ),
            (
                "3",
                None,
                "Arquitetura de software. Interoperabilidade de sistemas. Arquitetura e linguagem orientada a serviços. Web services. Mensageria. API, Swagger. Arquitetura e linguagem orientada a objetos. Arquitetura de aplicações para ambiente web. Servidor de aplicações. Servidor web.",
            ),
            (
                "4",
                None,
                "Ambientes Internet, extranet, intranet e portal: finalidades, características físicas e lógicas, aplicações e serviços.",
            ),
            ("5", None, "Padrões XML, XSLT, UDDI, REST e JSON."),
            ("6", None, "DevOps."),
            (
                "7",
                None,
                "Ferramenta de Gestão da configuração GIT. TESTES: conceitos básicos de testes de aplicações. Testes unitários. Testes de integração. Testes ágeis. Teste de usabilidade de software. Testes automatizados. Tipos de testes. Test-driven development (TDD). Gestão do ciclo de vida de testes.",
            ),
            ("7.1", "7", "RPA (robotic process automation)."),
            ("8", None, "Metodologias Ágeis de Desenvolvimento."),
            ("8.1", "8", "Scrum."),
            ("8.2", "8", "Kanban."),
            ("8.3", "8", "XP."),
            ("9", None, "Padrões de desenvolvimento e reuso."),
            (
                "10",
                None,
                "Codificação de software (transacionais, analíticos, mobile e API).",
            ),
            ("11", None, "Metodologia de Ponto de Função e Story Points."),
            ("12", None, "Engenharia de Requisitos."),
            ("12.1", "12", "Classificação de Requisitos."),
            ("12.2", "12", "Processo de Engenharia de Requisitos."),
            ("12.3", "12", "Técnicas de Elicitação de Requisitos."),
            (
                "13",
                None,
                "Tecnologias e práticas frontend web: HTML, CSS, UX, Ajax, frameworks (VueJS, Angular e React).",
            ),
            ("13.1", "13", "Padrões de frontend."),
            ("13.2", "13", "SPA e PWA."),
            ("14", None, "Protocolos HTTPS, SSL/TLS."),
            ("15", None, "Blockchain."),
            ("16", None, "Design de software."),
            (
                "17",
                None,
                "Arquitetura hexagonal, microsserviços (orquestração de serviços e API gateway) e containers.",
            ),
            ("18", None, "Transações distribuídas."),
            ("19", None, "User Experience (UX)."),
            ("19.1", "19", "Sistemas de gestão de conteúdo."),
            ("19.1.1", "19.1", "Conceitos básicos e aplicações."),
            ("19.1.2", "19.1", "Arquitetura de informação."),
            ("19.1.3", "19.1", "Portais corporativos."),
            ("19.1.4", "19.1", "Conceitos básicos e aplicações."),
            ("19.1.5", "19.1", "Workflow."),
            ("19.1.6", "19.1", "Conceitos de acessibilidade e usabilidade."),
            (
                "19.1.7",
                "19.1",
                "Desenho e planejamento de interação em aplicações web.",
            ),
            (
                "20",
                None,
                "Conceitos de Inteligência Artificial, Análise de Dados e Big Data.",
            ),
        ],
    },
    {
        "aliases": [
            "Inteligência de Negócios (Business Intelligence)",
            "Business Intelligence",
            "Inteligência de Negócios",
        ],
        "items": [
            (
                "1",
                None,
                "Conceitos, fundamentos, características, técnicas e métodos de business intelligence (BI).",
            ),
            ("2", None, "Sistemas de suporte a decisão e gestão de conteúdo."),
            (
                "3",
                None,
                "Arquitetura e aplicações de data warehouse com ETL e OLAP.",
            ),
            (
                "4",
                None,
                "Definições e conceitos de data warehouse e data mining.",
            ),
            ("5", None, "Visualização de dados: BD individuais e cubos."),
            (
                "6",
                None,
                "Mapeamento das fontes de dados: técnicas para coleta de dados.",
            ),
            ("7", None, "Arquitetura de business intelligence."),
        ],
    },
    {
        "aliases": ["Segurança da Informação"],
        "items": [
            ("1", None, "Políticas de segurança da informação."),
            (
                "2",
                None,
                "Procedimentos de segurança, conceitos gerais de gerenciamento.",
            ),
            (
                "3",
                None,
                "Normas ABNT NBR ISO/IEC 27001:2022 e ABNT NBR ISO/IEC 27002:2022.",
            ),
            ("4", None, "Confiabilidade, integridade e disponibilidade."),
            ("5", None, "Mecanismos de segurança."),
            (
                "5.1",
                "5",
                "Controle de acesso. Protocolo OAuth2. SSO (Single sign-on).",
            ),
            ("6", None, "Gerência de riscos."),
            ("6.1", "6", "Ameaça, vulnerabilidade e impacto."),
            (
                "7",
                None,
                "Ciclo de Vida de Desenvolvimento Seguro (SDL – Security Development Lifecycle), OWASP Top 10 (https://owasp.org/www-project-topten/).",
            ),
            (
                "8",
                None,
                "Análise estática e dinâmica de código (SAST – Static Application Security Testing e DAST – Dynamic Application Security Testing”).",
            ),
        ],
    },
    {
        "aliases": ["Banco de Dados"],
        "items": [
            ("1", None, "Modelagem de dados (conceitual, lógica e física)."),
            ("2", None, "Abordagem relacional e multidimensional."),
            ("3", None, "Normalização das estruturas de dados."),
            ("4", None, "Integridade referencial."),
            ("5", None, "Metadados."),
            ("6", None, "Modelagem dimensional."),
            ("7", None, "Linguagem de consulta estruturada (SQL)."),
            ("8", None, "Linguagem de definição de dados (DDL)."),
            ("9", None, "Linguagem de manipulação de dados (DML)."),
            ("10", None, "SGBD."),
            ("11", None, "Propriedades de banco de dados."),
            ("12", None, "Banco de dados NoSQL."),
            ("13", None, "Banco de dados em memória."),
            ("14", None, "Data lakes e soluções para big data."),
            ("15", None, "Dados Estruturados e não Estruturados."),
            ("16", None, "Avaliação de modelos de dados."),
            (
                "17",
                None,
                "Técnicas de Integração e Ingestão de Dados (ETL/ELT, Transferência de Arquivos e Integração via Base de Dados).",
            ),
        ],
    },
    {
        "aliases": [
            "Gestão e Governança de Tecnologia da Informação",
            "Gestão e Governança de TI",
            "Gestão/Governança TI",
        ],
        "items": [
            (
                "1",
                None,
                "Gerenciamento de projetos: conceitos; áreas de conhecimento, projetos, programas, portfólio, Tipos de Abordagem: tradicional, hibrida e ágil (Framework Scrum, Metodologia Lean, e Método Kanban); Guia Scrum de prática ágil para gerenciamento de projetos",
            ),
            (
                "2",
                None,
                "Processos, grupos de processos e área de conhecimento.",
            ),
            ("3", None, "Gestão de riscos."),
            ("4", None, "Gerenciamento de serviços (ITIL v4)."),
            (
                "4.1",
                "4",
                "Conceitos básicos, disciplinas, estrutura e objetivos.",
            ),
            ("5", None, "Governança de TI (COBIT 2019)."),
            (
                "5.1",
                "5",
                "Conceitos básicos, estrutura e objetivos.",
            ),
            (
                "6",
                None,
                "Conceitos de gestão de processos e modelagem de processos de negócio usando BPMN.",
            ),
        ],
    },
]


def normalized_aliases(entry):
    return {normalize_discipline_name(alias) for alias in entry["aliases"]}


class Command(BaseCommand):
    help = (
        "Importa os itens restantes do edital verticalizado do DATAPREV 2026 "
        "para um concurso já cadastrado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--competition",
            default="DATAPREV 2026",
            help="Nome exato do concurso. Padrão: DATAPREV 2026.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria importado sem gravar alterações.",
        )
        parser.add_argument(
            "--replace-existing",
            action="store_true",
            help=(
                "Apaga os itens existentes somente das disciplinas deste importador "
                "antes de recriá-los. Use com cuidado."
            ),
        )

    def handle(self, *args, **options):
        competition_name = options["competition"]
        dry_run = options["dry_run"]
        replace_existing = options["replace_existing"]

        try:
            competition = Competition.objects.get(name=competition_name)
        except Competition.DoesNotExist as exc:
            raise CommandError(
                f'Concurso "{competition_name}" não encontrado.'
            ) from exc
        except Competition.MultipleObjectsReturned as exc:
            raise CommandError(
                f'Existe mais de um concurso chamado "{competition_name}". '
                "Renomeie-os temporariamente ou use um nome único."
            ) from exc

        links = list(
            competition.discipline_links.select_related("discipline").order_by("position")
        )
        links_by_name = {
            normalize_discipline_name(link.discipline.name): link
            for link in links
        }

        plan = []
        missing = []

        for entry in SYLLABUS:
            link = next(
                (
                    links_by_name[alias]
                    for alias in normalized_aliases(entry)
                    if alias in links_by_name
                ),
                None,
            )
            if link is None:
                missing.append(entry["aliases"][0])
                continue

            existing_count = link.syllabus_items.count()
            if existing_count and not replace_existing:
                plan.append(
                    {
                        "link": link,
                        "items": entry["items"],
                        "action": "skip",
                        "existing_count": existing_count,
                    }
                )
                continue

            plan.append(
                {
                    "link": link,
                    "items": entry["items"],
                    "action": "replace" if existing_count else "create",
                    "existing_count": existing_count,
                }
            )

        for item in plan:
            link = item["link"]
            if item["action"] == "skip":
                self.stdout.write(
                    self.style.WARNING(
                        f'- {link.discipline.name}: ignorada '
                        f'({item["existing_count"]} item(ns) já cadastrado(s)).'
                    )
                )
            else:
                verb = "recriar" if item["action"] == "replace" else "criar"
                self.stdout.write(
                    f'- {link.discipline.name}: {verb} {len(item["items"])} item(ns).'
                )

        if missing:
            self.stdout.write(
                self.style.WARNING(
                    "Disciplinas não encontradas e que serão ignoradas: "
                    + ", ".join(missing)
                )
            )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run concluído; nada foi alterado."))
            return

        created_total = 0
        replaced_total = 0
        skipped_disciplines = 0

        with transaction.atomic():
            for item in plan:
                link = item["link"]

                if item["action"] == "skip":
                    skipped_disciplines += 1
                    continue

                if item["action"] == "replace":
                    replaced_total += link.syllabus_items.count()
                    link.syllabus_items.all().delete()

                created_by_code = {}
                for position, (code, parent_code, content) in enumerate(
                    item["items"],
                    start=1,
                ):
                    parent = created_by_code.get(parent_code) if parent_code else None
                    if parent_code and parent is None:
                        raise CommandError(
                            f"Pai {parent_code} não encontrado para {code} "
                            f"em {link.discipline.name}."
                        )

                    syllabus_item = SyllabusItem.objects.create(
                        competition_discipline=link,
                        item_code=code,
                        content=content,
                        parent=parent,
                        position=position,
                    )
                    created_by_code[code] = syllabus_item
                    created_total += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {created_total} item(ns) criado(s)."
            )
        )
        if replaced_total:
            self.stdout.write(
                f"{replaced_total} item(ns) antigo(s) foram substituído(s)."
            )
        if skipped_disciplines:
            self.stdout.write(
                f"{skipped_disciplines} disciplina(s) com conteúdo existente foram preservadas."
            )

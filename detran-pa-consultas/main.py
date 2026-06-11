import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint

from services.sistransito import SistransitoService
from services.renach import RenachService
from services.captcha_solver import CaptchaSolver

console = Console()


def print_result(result: dict):
    if "erro" in result:
        console.print(f"\n[bold red]ERRO:[/bold red] {result['erro']}")
        return

    console.print(f"\n[bold cyan]{result.get('tipo', 'Resultado')}[/bold cyan]")

    dados = result.get("dados", {})
    if dados:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="green")

        for key, value in dados.items():
            if isinstance(value, dict):
                console.print(f"\n[bold yellow]{key}[/bold yellow]")
                for k, v in value.items():
                    table.add_row(str(k), str(v))
            else:
                table.add_row(str(key), str(value))

        console.print(table)

    if "tabelas" in result:
        for i, tbl in enumerate(result.get("tabelas", [])):
            console.print(f"\n[bold yellow]Tabela {i+1}[/bold yellow]")
            row_table = Table(show_header=True, header_style="bold magenta")
            if tbl:
                for key in tbl[0].keys() if isinstance(tbl, list) and tbl else []:
                    row_table.add_column(key)
                for row in tbl if isinstance(tbl, list) else [tbl]:
                    row_table.add_row(*[str(v) for v in (row.values() if isinstance(row, dict) else [])])
                console.print(row_table)

    if "infracoes" in result:
        for i, inf in enumerate(result["infracoes"]):
            console.print(f"\n[bold yellow]Infração {i+1}[/bold yellow]")
            inf_table = Table(show_header=True, header_style="bold red")
            for key in inf.keys():
                inf_table.add_column(key)
            inf_table.add_row(*[str(v) for v in inf.values()])
            console.print(inf_table)

    if "pdf_link" in result:
        console.print(f"\n[bold green]PDF disponível em:[/bold green] {result['pdf_link']}")

    if "alerta" in result:
        console.print(f"\n[bold yellow]ALERTA:[/bold yellow] {result['alerta']}")


def save_result(result: dict, prefix: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"exports/{prefix}_{ts}.json"
    os.makedirs("exports", exist_ok=True)

    save_data = {k: v for k, v in result.items() if k != "html"}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
    console.print(f"[green]Resultado salvo em:[/green] {filename}")
    return filename


def save_html(result: dict, prefix: str):
    if "html" not in result:
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"exports/{prefix}_{ts}.html"
    os.makedirs("exports", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result["html"])
    console.print(f"[green]HTML salvo em:[/green] {filename}")
    return filename


def main():
    console.print(Panel.fit(
        "[bold blue]DETRAN-PA - Sistema de Consultas[/bold blue]\n"
        "[dim]Consultas de Veículo, Infrações, Licenciamento e CNH[/dim]",
        border_style="blue"
    ))

    captcha_solver = CaptchaSolver()
    sistransito = SistransitoService(captcha_solver)
    renach = RenachService(captcha_solver)

    while True:
        console.print("\n[bold]═══ MENU PRINCIPAL ═══[/bold]\n")
        console.print("[1] 🚗 Consulta Veículo Detalhada (Placa + Renavam)")
        console.print("[2] 📋 Consulta Infrações (Placa + Renavam)")
        console.print("[3] 📄 Boleto Licenciamento Ano Atual")
        console.print("[4] 📄 Boleto Licenciamento Ano Anterior")
        console.print("[5] 📄 Boleto Infração (Veículos do Pará)")
        console.print("[6] 🔍 Consulta Gravame (Chassi)")
        console.print("[7] 📑 Emissão CRLV-e")
        console.print("[8] 📁 Acompanhe seu Documento")
        console.print("[9] 🪪 Consulta Pontuação CNH")
        console.print("[0] 🚪 Sair")

        opcao = Prompt.ask("\nEscolha", choices=["0","1","2","3","4","5","6","7","8","9"], default="0")

        if opcao == "0":
            console.print("[bold red]Saindo...[/bold red]")
            break

        try:
            if opcao == "1":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                with console.status("[bold cyan]Consultando veículo... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.consulta_veiculo(placa, renavam)
                print_result(result)
                save_result(result, "veiculo")
                save_html(result, "veiculo")

            elif opcao == "2":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                with console.status("[bold cyan]Consultando infrações... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.consulta_infracoes(placa, renavam)
                print_result(result)
                save_result(result, "infracoes")
                save_html(result, "infracoes")

            elif opcao == "3":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                salvar = Prompt.ask("Salvar PDF? (s/n)", default="s")
                pdf_path = f"exports/licenciamento_atual_{placa}.pdf" if salvar.lower() == "s" else None
                with console.status("[bold cyan]Consultando licenciamento atual... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.boleto_licenciamento_atual(placa, renavam, salvar_pdf=pdf_path)
                print_result(result)
                save_result(result, "licenc_atual")
                save_html(result, "licenc_atual")

            elif opcao == "4":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                salvar = Prompt.ask("Salvar PDF? (s/n)", default="s")
                pdf_path = f"exports/licenciamento_anterior_{placa}.pdf" if salvar.lower() == "s" else None
                with console.status("[bold cyan]Consultando licenciamento anterior... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.boleto_licenciamento_anterior(placa, renavam, salvar_pdf=pdf_path)
                print_result(result)
                save_result(result, "licenc_anterior")
                save_html(result, "licenc_anterior")

            elif opcao == "5":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                with console.status("[bold cyan]Consultando boleto infração... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.boleto_infracao(placa, renavam, veiculo_para=True)
                print_result(result)
                save_result(result, "boleto_infracao")
                save_html(result, "boleto_infracao")

            elif opcao == "6":
                chassi = Prompt.ask("Chassi").upper()
                with console.status("[bold cyan]Consultando gravame... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.gravame(chassi)
                print_result(result)
                save_result(result, "gravame")
                save_html(result, "gravame")

            elif opcao == "7":
                placa = Prompt.ask("Placa").upper()
                renavam = Prompt.ask("Renavam")
                cpf_cnpj = Prompt.ask("CPF/CNPJ")
                with console.status("[bold cyan]Emitindo CRLV-e... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.crlv_e(placa, renavam, cpf_cnpj)
                print_result(result)
                save_result(result, "crlv_e")
                save_html(result, "crlv_e")

            elif opcao == "8":
                modo = Prompt.ask("Modo (P=Renavam, C=Chassi)", choices=["P", "C"], default="P")
                if modo == "P":
                    renavam = Prompt.ask("Renavam")
                    chassi = None
                else:
                    chassi = Prompt.ask("Chassi").upper()
                    renavam = None
                no_boleto = Prompt.ask("Número do Boleto (vazio para último)", default="")
                with console.status("[bold cyan]Acompanhando documento... Resolvendo CAPTCHA...[/bold cyan]"):
                    result = sistransito.acompanha_documento(
                        renavam=renavam, chassi=chassi,
                        no_boleto=no_boleto if no_boleto else None,
                        modo=modo
                    )
                print_result(result)
                save_result(result, "acompanha_doc")
                save_html(result, "acompanha_doc")

            elif opcao == "9":
                cpf = Prompt.ask("CPF")
                with console.status("[bold cyan]Consultando pontuação CNH... Resolvendo CAPTCHA de imagem...[/bold cyan]"):
                    result = renach.consulta_pontuacao_cnh(cpf)
                print_result(result)
                save_result(result, "cnh_pontuacao")
                save_html(result, "cnh_pontuacao")

        except RuntimeError as e:
            console.print(f"\n[bold red]ERRO:[/bold red] {e}")
        except TimeoutError as e:
            console.print(f"\n[bold red]TIMEOUT:[/bold red] {e}")
        except Exception as e:
            console.print(f"\n[bold red]ERRO INESPERADO:[/bold red] {e}")
            console.print_exception()


if __name__ == "__main__":
    main()
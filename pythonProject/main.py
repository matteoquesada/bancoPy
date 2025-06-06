#!/usr/bin/env python3
"""
SINPE Banking System - Main Entry Point
Terminal-based banking application with Flask API backend
"""

import os
import sys
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import box

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db
from app.services.database_service import DatabaseService
from app.services.terminal_service import TerminalService

console = Console()

class SinpeBankingSystem:
    def __init__(self):
        self.app = create_app()
        self.terminal_service = TerminalService()
        self.current_user = None
        self.server_thread = None
        self.server_running = False
        
    def initialize_database(self):
        """Initialize database with sample data"""
        console.print("[yellow]Initializing database...[/yellow]")
        
        with self.app.app_context():
            db.create_all()
            db_service = DatabaseService()
            db_service.create_sample_data()
            
        console.print("[green]✓ Database initialized successfully[/green]")
    
    def start_api_server(self):
        """Start Flask API server in background thread"""
        def run_server():
            self.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_running = True
        time.sleep(2)  # Give server time to start
        
    def show_welcome_screen(self):
        """Display welcome screen"""
        console.clear()
        
        welcome_text = Text()
        welcome_text.append("SINPE", style="bold blue")
        welcome_text.append(" Banking System", style="bold white")
        
        panel = Panel(
            welcome_text,
            title="🏦 Welcome",
            title_align="center",
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print("\n[dim]Costa Rican Payment System - Python Implementation[/dim]")
        console.print("[dim]API Server running on http://127.0.0.1:5000[/dim]\n")
    
    def show_main_menu(self):
        """Display main menu options"""
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Description", style="white")
        
        table.add_row("1", "🔐 Login / User Management")
        table.add_row("2", "💰 Account Management")
        table.add_row("3", "📱 SINPE Transfer")
        table.add_row("4", "📊 Transaction History")
        table.add_row("5", "🔗 Phone Link Management")
        table.add_row("6", "⚙️  Admin Panel")
        table.add_row("7", "🌐 API Documentation")
        table.add_row("0", "❌ Exit")
        
        console.print(table)
        
    def handle_menu_choice(self, choice):
        """Handle main menu selection"""
        if choice == "1":
            self.terminal_service.show_user_management()
        elif choice == "2":
            self.terminal_service.show_account_management()
        elif choice == "3":
            self.terminal_service.show_sinpe_transfer()
        elif choice == "4":
            self.terminal_service.show_transaction_history()
        elif choice == "5":
            self.terminal_service.show_phone_link_management()
        elif choice == "6":
            self.terminal_service.show_admin_panel()
        elif choice == "7":
            self.show_api_documentation()
        elif choice == "0":
            return False
        else:
            console.print("[red]Invalid option. Please try again.[/red]")
            
        return True
    
    def show_api_documentation(self):
        """Show API endpoints documentation"""
        console.clear()
        console.print(Panel("🌐 API Documentation", style="bold blue"))
        
        endpoints = [
            ("POST", "/api/sinpe-movil", "Handle SINPE transfers"),
            ("GET", "/api/validate/{phone}", "Validate phone number"),
            ("GET", "/api/sinpe/user-link/{username}", "Check user SINPE link"),
            ("GET", "/api/users", "List all users"),
            ("POST", "/api/users", "Create new user"),
            ("GET", "/api/accounts", "List all accounts"),
            ("POST", "/api/accounts", "Create new account"),
            ("GET", "/api/transactions", "List transactions"),
            ("POST", "/api/phone-links", "Create phone link"),
        ]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Method", style="green", width=8)
        table.add_column("Endpoint", style="cyan")
        table.add_column("Description", style="white")
        
        for method, endpoint, description in endpoints:
            table.add_row(method, endpoint, description)
            
        console.print(table)
        console.print(f"\n[dim]Base URL: http://127.0.0.1:5000[/dim]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def run(self):
        """Main application loop"""
        try:
            # Initialize system
            self.show_welcome_screen()
            console.print("[yellow]Starting SINPE Banking System...[/yellow]")
            
            # Initialize database
            self.initialize_database()
            
            # Start API server
            console.print("[yellow]Starting API server...[/yellow]")
            self.start_api_server()
            console.print("[green]✓ API server started on http://127.0.0.1:5000[/green]")
            
            # Main menu loop
            while True:
                console.print("\n" + "="*60)
                self.show_main_menu()
                
                choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", default="0")
                
                if not self.handle_menu_choice(choice):
                    break
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            console.print("[green]Thank you for using SINPE Banking System![/green]")

if __name__ == "__main__":
    system = SinpeBankingSystem()
    system.run()
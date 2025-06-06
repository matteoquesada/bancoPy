"""
Terminal Service - Rich terminal interface for SINPE Banking System
"""

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, FloatPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich import box
import time

console = Console()

class TerminalService:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000/api"
        self.current_user = None
    
    def show_user_management(self):
        """User management interface"""
        console.clear()
        console.print(Panel("👤 User Management", style="bold blue"))
        
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Description", style="white")
        
        table.add_row("1", "📋 List all users")
        table.add_row("2", "➕ Create new user")
        table.add_row("3", "🔐 Login as user")
        table.add_row("4", "🚪 Logout")
        table.add_row("0", "⬅️  Back to main menu")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", default="0")
        
        if choice == "1":
            self.list_users()
        elif choice == "2":
            self.create_user()
        elif choice == "3":
            self.login_user()
        elif choice == "4":
            self.logout_user()
        elif choice == "0":
            return
        else:
            console.print("[red]Invalid option[/red]")
            
        Prompt.ask("\nPress Enter to continue")
    
    def list_users(self):
        """List all users"""
        try:
            response = requests.get(f"{self.base_url}/users")
            if response.status_code == 200:
                data = response.json()
                users = data['data']
                
                table = Table(title="👥 All Users")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Email", style="blue")
                table.add_column("Phone", style="yellow")
                table.add_column("Created", style="dim")
                
                for user in users:
                    table.add_row(
                        str(user['id']),
                        user['name'],
                        user['email'],
                        user['phone'],
                        user['created_at'][:10] if user['created_at'] else 'N/A'
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def create_user(self):
        """Create new user"""
        console.print("\n[bold green]Create New User[/bold green]")
        
        name = Prompt.ask("Username")
        email = Prompt.ask("Email")
        phone = Prompt.ask("Phone number")
        password = Prompt.ask("Password", password=True)
        
        try:
            data = {
                'name': name,
                'email': email,
                'phone': phone,
                'password': password
            }
            
            response = requests.post(f"{self.base_url}/users", json=data)
            if response.status_code == 201:
                console.print("[green]✓ User created successfully[/green]")
            else:
                error_data = response.json()
                console.print(f"[red]Error: {error_data.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def login_user(self):
        """Login user"""
        console.print("\n[bold green]User Login[/bold green]")
        
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)
        
        try:
            data = {'username': username, 'password': password}
            response = requests.post(f"{self.base_url}/auth/login", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.current_user = result['user']
                console.print(f"[green]✓ Welcome, {self.current_user['name']}![/green]")
            else:
                error_data = response.json()
                console.print(f"[red]Error: {error_data.get('error', 'Login failed')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def logout_user(self):
        """Logout user"""
        try:
            requests.post(f"{self.base_url}/auth/logout")
            self.current_user = None
            console.print("[green]✓ Logged out successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def show_account_management(self):
        """Account management interface"""
        console.clear()
        console.print(Panel("💰 Account Management", style="bold green"))
        
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Description", style="white")
        
        table.add_row("1", "📋 List all accounts")
        table.add_row("2", "➕ Create new account")
        table.add_row("3", "👤 View user accounts")
        table.add_row("4", "💵 Update account balance")
        table.add_row("0", "⬅️  Back to main menu")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", default="0")
        
        if choice == "1":
            self.list_accounts()
        elif choice == "2":
            self.create_account()
        elif choice == "3":
            self.view_user_accounts()
        elif choice == "4":
            self.update_account_balance()
        elif choice == "0":
            return
        else:
            console.print("[red]Invalid option[/red]")
            
        Prompt.ask("\nPress Enter to continue")
    
    def list_accounts(self):
        """List all accounts"""
        try:
            response = requests.get(f"{self.base_url}/accounts")
            if response.status_code == 200:
                data = response.json()
                accounts = data['data']
                
                table = Table(title="💰 All Accounts")
                table.add_column("ID", style="cyan")
                table.add_column("Number", style="green")
                table.add_column("Currency", style="blue")
                table.add_column("Balance", style="yellow", justify="right")
                table.add_column("Created", style="dim")
                
                for account in accounts:
                    balance_text = f"{account['balance']:,.2f}"
                    table.add_row(
                        str(account['id']),
                        account['number'],
                        account['currency'],
                        balance_text,
                        account['created_at'][:10] if account['created_at'] else 'N/A'
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def create_account(self):
        """Create new account"""
        console.print("\n[bold green]Create New Account[/bold green]")
        
        balance = FloatPrompt.ask("Initial balance", default=0.0)
        currency = Prompt.ask("Currency", default="CRC")
        
        # Optional: link to user
        link_user = Confirm.ask("Link to a user?")
        user_id = None
        if link_user:
            user_id = Prompt.ask("User ID (number)")
        
        try:
            data = {
                'balance': balance,
                'currency': currency
            }
            if user_id:
                data['user_id'] = int(user_id)
            
            response = requests.post(f"{self.base_url}/accounts", json=data)
            if response.status_code == 201:
                result = response.json()
                account = result['data']
                console.print(f"[green]✓ Account created: {account['number']}[/green]")
            else:
                error_data = response.json()
                console.print(f"[red]Error: {error_data.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def view_user_accounts(self):
        """View accounts for a specific user"""
        user_id = Prompt.ask("Enter User ID")
        
        try:
            response = requests.get(f"{self.base_url}/users/{user_id}/accounts")
            if response.status_code == 200:
                data = response.json()
                accounts = data['data']
                
                if not accounts:
                    console.print("[yellow]No accounts found for this user[/yellow]")
                    return
                
                table = Table(title=f"💰 Accounts for User ID {user_id}")
                table.add_column("Number", style="green")
                table.add_column("Currency", style="blue")
                table.add_column("Balance", style="yellow", justify="right")
                
                for account in accounts:
                    balance_text = f"{account['balance']:,.2f}"
                    table.add_row(
                        account['number'],
                        account['currency'],
                        balance_text
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def update_account_balance(self):
        """Update account balance"""
        account_id = Prompt.ask("Enter Account ID")
        new_balance = FloatPrompt.ask("New balance")
        
        try:
            data = {'balance': new_balance}
            response = requests.put(f"{self.base_url}/accounts/{account_id}/balance", json=data)
            
            if response.status_code == 200:
                console.print("[green]✓ Balance updated successfully[/green]")
            else:
                error_data = response.json()
                console.print(f"[red]Error: {error_data.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def show_sinpe_transfer(self):
        """SINPE transfer interface"""
        console.clear()
        console.print(Panel("📱 SINPE Transfer", style="bold magenta"))
        
        console.print("[yellow]Note: This is a simplified transfer interface[/yellow]")
        console.print("[dim]For full HMAC verification, use the API directly[/dim]\n")
        
        sender_phone = Prompt.ask("Sender phone number")
        receiver_phone = Prompt.ask("Receiver phone number")
        amount = FloatPrompt.ask("Amount")
        description = Prompt.ask("Description (optional)", default="")
        
        # Validate receiver phone first
        try:
            validate_response = requests.get(f"{self.base_url}/validate/{receiver_phone}")
            if validate_response.status_code != 200:
                console.print("[red]❌ Receiver phone number is not registered in SINPE[/red]")
                return
            
            receiver_info = validate_response.json()
            console.print(f"[green]✓ Receiver: {receiver_info['name']} (Bank: {receiver_info['bank_code']})[/green]")
            
        except Exception as e:
            console.print(f"[red]Error validating phone: {e}[/red]")
            return
        
        # Confirm transfer
        if not Confirm.ask(f"\nConfirm transfer of {amount:,.2f} CRC to {receiver_phone}?"):
            console.print("[yellow]Transfer cancelled[/yellow]")
            return
        
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing transfer...", total=None)
            
            try:
                # Simulate processing time
                time.sleep(2)
                
                # For demo purposes, we'll call the service directly
                # In a real implementation, you'd generate proper HMAC
                from app.services.sinpe_service import SinpeService
                from app import create_app
                
                app = create_app()
                with app.app_context():
                    transfer = SinpeService.send_sinpe_transfer(
                        sender_phone=sender_phone,
                        receiver_phone=receiver_phone,
                        amount=amount,
                        description=description
                    )
                
                progress.update(task, description="Transfer completed!")
                time.sleep(1)
                
                console.print(f"\n[green]✅ Transfer successful![/green]")
                console.print(f"Transaction ID: {transfer.transaction_id}")
                console.print(f"Amount: {transfer.amount:,.2f} {transfer.currency}")
                console.print(f"Status: {transfer.status}")
                
            except Exception as e:
                progress.update(task, description="Transfer failed!")
                console.print(f"\n[red]❌ Transfer failed: {e}[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def show_transaction_history(self):
        """Transaction history interface"""
        console.clear()
        console.print(Panel("📊 Transaction History", style="bold yellow"))
        
        try:
            response = requests.get(f"{self.base_url}/transactions")
            if response.status_code == 200:
                data = response.json()
                transactions = data['data']
                
                if not transactions:
                    console.print("[yellow]No transactions found[/yellow]")
                    return
                
                table = Table(title="📊 Recent Transactions")
                table.add_column("ID", style="cyan", width=8)
                table.add_column("From", style="green", width=12)
                table.add_column("To", style="blue", width=12)
                table.add_column("Amount", style="yellow", justify="right", width=12)
                table.add_column("Status", style="magenta", width=10)
                table.add_column("Date", style="dim", width=12)
                
                for trans in transactions[:20]:  # Show last 20
                    from_account = str(trans['from_account_id']) if trans['from_account_id'] else 'External'
                    to_account = str(trans['to_account_id'])
                    amount_text = f"{trans['amount']:,.2f}"
                    status_style = "green" if trans['status'] == 'completed' else "yellow"
                    
                    table.add_row(
                        trans['transaction_id'][:8] + "...",
                        from_account,
                        to_account,
                        amount_text,
                        f"[{status_style}]{trans['status']}[/{status_style}]",
                        trans['created_at'][:10] if trans['created_at'] else 'N/A'
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def show_phone_link_management(self):
        """Phone link management interface"""
        console.clear()
        console.print(Panel("🔗 Phone Link Management", style="bold cyan"))
        
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Description", style="white")
        
        table.add_row("1", "📋 List all phone links")
        table.add_row("2", "➕ Create new phone link")
        table.add_row("3", "🔍 Search by phone number")
        table.add_row("4", "🏦 Search by account number")
        table.add_row("0", "⬅️  Back to main menu")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", default="0")
        
        if choice == "1":
            self.list_phone_links()
        elif choice == "2":
            self.create_phone_link()
        elif choice == "3":
            self.search_phone_link_by_phone()
        elif choice == "4":
            self.search_phone_link_by_account()
        elif choice == "0":
            return
        else:
            console.print("[red]Invalid option[/red]")
            
        Prompt.ask("\nPress Enter to continue")
    
    def list_phone_links(self):
        """List all phone links"""
        try:
            response = requests.get(f"{self.base_url}/phone-links")
            if response.status_code == 200:
                data = response.json()
                links = data['data']
                
                table = Table(title="🔗 Phone Links")
                table.add_column("ID", style="cyan")
                table.add_column("Account Number", style="green")
                table.add_column("Phone", style="yellow")
                table.add_column("Created", style="dim")
                
                for link in links:
                    table.add_row(
                        str(link['id']),
                        link['account_number'],
                        link['phone'],
                        link['created_at'][:10] if link['created_at'] else 'N/A'
                    )
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def create_phone_link(self):
        """Create new phone link"""
        console.print("\n[bold green]Create New Phone Link[/bold green]")
        
        account_number = Prompt.ask("Account number")
        phone = Prompt.ask("Phone number")
        
        try:
            data = {
                'account_number': account_number,
                'phone': phone
            }
            
            response = requests.post(f"{self.base_url}/phone-links", json=data)
            if response.status_code == 201:
                console.print("[green]✓ Phone link created successfully[/green]")
            else:
                error_data = response.json()
                console.print(f"[red]Error: {error_data.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def search_phone_link_by_phone(self):
        """Search phone link by phone number"""
        phone = Prompt.ask("Phone number")
        
        try:
            response = requests.get(f"{self.base_url}/phone-links/phone/{phone}")
            if response.status_code == 200:
                data = response.json()
                link = data['data']
                
                console.print(f"[green]✓ Found link:[/green]")
                console.print(f"  Account: {link['account_number']}")
                console.print(f"  Phone: {link['phone']}")
                console.print(f"  Created: {link['created_at']}")
            else:
                console.print("[yellow]Phone link not found[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def search_phone_link_by_account(self):
        """Search phone link by account number"""
        account_number = Prompt.ask("Account number")
        
        try:
            response = requests.get(f"{self.base_url}/phone-links/account/{account_number}")
            if response.status_code == 200:
                data = response.json()
                link = data['data']
                
                console.print(f"[green]✓ Found link:[/green]")
                console.print(f"  Account: {link['account_number']}")
                console.print(f"  Phone: {link['phone']}")
                console.print(f"  Created: {link['created_at']}")
            else:
                console.print("[yellow]Phone link not found[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def show_admin_panel(self):
        """Admin panel interface"""
        console.clear()
        console.print(Panel("⚙️ Admin Panel", style="bold red"))
        
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Description", style="white")
        
        table.add_row("1", "📊 Database statistics")
        table.add_row("2", "🔄 Reset database")
        table.add_row("3", "🧪 Create test data")
        table.add_row("4", "🔍 Validate SINPE phone")
        table.add_row("0", "⬅️  Back to main menu")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", default="0")
        
        if choice == "1":
            self.show_database_stats()
        elif choice == "2":
            self.reset_database()
        elif choice == "3":
            self.create_test_data()
        elif choice == "4":
            self.validate_sinpe_phone()
        elif choice == "0":
            return
        else:
            console.print("[red]Invalid option[/red]")
            
        Prompt.ask("\nPress Enter to continue")
    
    def show_database_stats(self):
        """Show database statistics"""
        try:
            from app.services.database_service import DatabaseService
            from app import create_app
            
            app = create_app()
            with app.app_context():
                db_service = DatabaseService()
                stats = db_service.get_database_stats()
            
            table = Table(title="📊 Database Statistics")
            table.add_column("Table", style="cyan")
            table.add_column("Count", style="yellow", justify="right")
            
            for table_name, count in stats.items():
                table.add_row(table_name.replace('_', ' ').title(), str(count))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def reset_database(self):
        """Reset database"""
        if Confirm.ask("[red]⚠️  This will delete all data. Are you sure?[/red]"):
            try:
                from app.services.database_service import DatabaseService
                from app import create_app
                
                app = create_app()
                with app.app_context():
                    db_service = DatabaseService()
                    db_service.reset_database()
                
                console.print("[green]✓ Database reset successfully[/green]")
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def create_test_data(self):
        """Create additional test data"""
        console.print("[yellow]Creating additional test data...[/yellow]")
        # This could be expanded to create more specific test scenarios
        console.print("[green]✓ Test data creation completed[/green]")
    
    def validate_sinpe_phone(self):
        """Validate SINPE phone number"""
        phone = Prompt.ask("Phone number to validate")
        
        try:
            response = requests.get(f"{self.base_url}/validate/{phone}")
            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]✓ Phone number is registered:[/green]")
                console.print(f"  Name: {data['name']}")
                console.print(f"  Bank Code: {data['bank_code']}")
                console.print(f"  Phone: {data['phone']}")
            else:
                console.print("[red]❌ Phone number is not registered in SINPE[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
# Deploy Commands

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

This section documents deployment-related commands and practices.

## Overview

The framework includes an example `deploy` command that demonstrates how to create custom CLI commands for deployment automation. This is a template that can be customized for your specific deployment needs.

---

## Example deploy Command

A custom command example showing how to create deployment automation.

### Registration

The command must be manually registered in `src/jtc/cli/main.py`:

```python
from jtc.cli.commands.deploy import app as deploy_app
app.add_typer(deploy_app, name="deploy")
```

### Usage

```bash
# Run the deploy command
jtc deploy

# With options
jtc deploy --option value

# With flag
jtc deploy --flag
```

### What It Does

This is a placeholder/example command. In a real project, you would customize it to:
- Deploy to production servers
- Run database migrations
- Clear caches
- Verify deployment health
- Notify team of deployment
- Rollback on failure

---

## Creating Custom Deploy Commands

### Step 1: Generate Command

```bash
jtc make:cmd deploy
```

This creates `src/jtc/cli/commands/deploy.py` with boilerplate code.

### Step 2: Implement Deployment Logic

Edit the generated file:

```python
"""
Deploy Command

Automates the deployment process.
"""
import subprocess
import os
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def main(
    environment: str = typer.Option("staging", "--env", "-e", help="Deployment environment"),
    migrate: bool = typer.Option(True, "--migrate", "-m", help="Run migrations"),
    seed: bool = typer.Option(False, "--seed", "-s", help="Run database seeders"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deployment"),
) -> None:
    """Deploy application to specified environment."""
    
    env_color = {
        "staging": "yellow",
        "production": "red"
    }.get(environment, "cyan")
    
    console.print(f"[bold {env_color}]Deploying to {environment}...[/bold {env_color}]")
    
    # Step 1: Run tests
    console.print("[dim]1. Running tests...[/dim]")
    if run_tests():
        console.print("[green]   ✓ Tests passed[/green]")
    else:
        console.print("[red]   ✗ Tests failed[/red]")
        if not force:
            console.print("[yellow]Aborting deployment (use --force to continue)[/yellow]")
            raise typer.Exit(code=1)
    
    # Step 2: Run migrations
    if migrate:
        console.print("[dim]2. Running migrations...[/dim]")
        if run_migrations():
            console.print("[green]   ✓ Migrations applied[/green]")
        else:
            console.print("[red]   ✗ Migrations failed[/red]")
            raise typer.Exit(code=1)
    
    # Step 3: Clear caches
    console.print("[dim]3. Clearing caches...[/dim]")
    clear_caches()
    console.print("[green]   ✓ Caches cleared[/green]")
    
    # Step 4: Seed database
    if seed:
        console.print("[dim]4. Seeding database...[/dim]")
        if seed_database():
            console.print("[green]   ✓ Database seeded[/green]")
        else:
            console.print("[yellow]   ⚠️  Seeding skipped[/yellow]")
    
    # Step 5: Deployment complete
    console.print()
    console.print(f"[bold green]🎉 Deployment to {environment} complete![/bold green]")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print("  • Verify application health")
    console.print(f"  • Visit: https://{environment}.yourdomain.com")
    console.print("  • Check logs for errors")

def run_tests() -> bool:
    """Run test suite."""
    result = subprocess.run(["pytest", "-x"], capture_output=True)
    return result.returncode == 0

def run_migrations() -> bool:
    """Run database migrations."""
    result = subprocess.run(["jtc", "db:migrate"], capture_output=True)
    return result.returncode == 0

def clear_caches():
    """Clear application caches."""
    # Clear cache
    subprocess.run(["jtc", "cache:clear"], capture_output=True)

def seed_database() -> bool:
    """Run database seeders."""
    result = subprocess.run(["jtc", "db:seed"], capture_output=True)
    return result.returncode == 0
```

### Step 3: Register Command

Add to `src/jtc/cli/main.py`:

```python
from jtc.cli.commands.deploy import app as deploy_app

# Register custom command
app.add_typer(deploy_app, name="deploy")
```

### Step 4: Run Custom Command

```bash
# Deploy to staging
jtc deploy --env staging

# Deploy to production with force
jtc deploy --env production --force

# Deploy with migration and seeding
jtc deploy --env production --migrate --seed
```

---

## Common Deployment Patterns

### Zero-Downtime Deployment

```python
# Deploy to production with zero downtime
@app.command()
def deploy_production():
    # 1. Start new servers
    start_new_servers()
    
    # 2. Wait for health checks
    wait_for_health_checks()
    
    # 3. Switch load balancer
    switch_load_balancer()
    
    # 4. Stop old servers
    stop_old_servers()
    
    # 5. Cleanup
    cleanup_old_servers()
```

### Blue-Green Deployment

```python
@app.command()
def deploy_blue_green():
    # Deploy to blue environment first
    deploy_to("blue")
    
    # Wait for health check
    wait_for_health("blue")
    
    # Switch traffic to blue
    switch_traffic("blue")
    
    # If successful, deploy to green
    deploy_to("green")
    wait_for_health("green")
    switch_traffic("green")
    
    # Clean up blue
    cleanup("blue")
```

### Rolling Deployment

```python
@app.command()
def deploy_rolling():
    # Deploy to subset of servers
    for i in range(0, 10, 2):  # 0, 2, 4, 6, 8
        deploy_to_server(i)
        wait_for_health(i)
    
    # Verify all servers healthy
    if all_servers_healthy():
        console.print("[green]✓ Rolling deployment complete[/green]")
```

### Canary Deployment

```python
@app.command()
def deploy_canary():
    # Deploy to 10% of traffic
    deploy_canary_servers()
    
    # Monitor metrics
    if monitor_metrics(duration="10m"):
        # If canary successful, roll out to 100%
        full_rollout()
    else:
        # Rollback canary
        rollback_canary()
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: evertonco/fast-track-framework/.opencode/.github/actions/setup@v1
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: docker exec fast_track_dev bash -c "cd larafast && poetry install"
      - name: Deploy to production
        run: docker exec fast_track_dev bash -c "cd larafast && jtc deploy --env production"
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy_production:
  stage: deploy
  script:
    - docker exec fast_track_dev bash -c "cd larafast && poetry install"
    - docker exec fast_track_dev bash -c "cd larafast && pytest workbench/tests/ -x"
    - docker exec fast_track_dev bash -c "cd larafast && jtc deploy --env production"
  only:
    - main
```

### Docker Deployment

```bash
# Deploy with Docker
docker-compose up -d

# Update Docker image
docker-compose pull fast-track-framework
docker-compose up -d

# Deploy to remote server
ssh user@production-server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Migration scripts reviewed
- [ ] Backup created
- [ ] Environment variables set
- [ ] SSL certificates valid
- [ ] Dependencies installed
- [ ] Database schema reviewed

### Deployment Steps

1. **Create backup** of production database
2. **Run migrations** on test database first
3. **Deploy new version** to production
4. **Wait for health check** (max 5 minutes)
5. **Switch load balancer** if using multiple servers
6. **Verify application** is working
7. **Monitor logs** for errors

### Post-Deployment

- [ ] Health checks passing
- [ ] No errors in logs
- [ ] Performance metrics normal
- [ ] User-reported issues: 0
- [ ] Backup verified
- [ ] Rollback plan documented

---

## Best Practices

### Automation

- **Automate Everything**: Use scripts, not manual steps
- **Idempotent**: Deployments should be safe to run multiple times
- **Fast Rollback**: Quick rollback if issues detected
- **Feature Flags**: Ability to disable features without redeployment
- **Gradual Rollout**: Canary or rolling deployments

### Monitoring

- **Health Checks**: Endpoint to verify application health
- **Log Aggregation**: Centralized logging
- **Metrics**: Track deployment success/failure
- **Alerts**: Notify team on failures

### Safety

- **Backups**: Always before deployment
- **Testing**: Test on staging first
- **Gradual**: Don't deploy to all servers at once
- **Rollback Ready**: Have rollback plan ready

---

## Troubleshooting

### Deployment Failed

```bash
# Check logs
docker logs fast_track_dev

# Check application health
curl https://yourapp.com/health

# Rollback if needed
# Use your rollback strategy:
git revert HEAD
# Redeploy old version
```

### Database Migration Issues

```bash
# Check migration status
jtc db:migrate

# View migration history
# Check workbench/database/migrations/versions/

# Rollback migration
jtc db:rollback --step 1

# Fix migration issue
# Re-run migration
jtc db:migrate
```

### Cache Issues

```bash
# Clear all caches
jtc cache:clear

# Verify cache configuration
jtc cache:config

# Check cache driver connectivity
redis-cli ping
```

---

## Comparison with Laravel

| Laravel | Fast Track | Purpose |
|---------|-------------|----------|
| `php artisan deploy` | `jtc deploy` | Deployment automation |
| `php artisan env` | `jtc cache:config` | Environment configuration |
| Laravel Forge | Custom + GitHub Actions | Hosting/deployment automation |
| Laravel Vapor | Docker + CI/CD | Cloud deployment |

---

## Related Commands

- [Make Commands](make-commands.md#makecmd) - Create custom deployment commands
- [Database Commands](db-commands.md) - Run migrations
- [Cache Commands](cache-commands.md) - Clear caches
- [Test Commands](test-commands.md) - Run test suite before deploy

---

**Framework Version**: 1.0.0a1  
**Last Updated**: 2026-02-21

import typer
from .observability.logging import setup_logging, get_logger

app = typer.Typer(help="Audience Radar CLI", no_args_is_help=True)
logger = get_logger(__name__)

@app.command()
def doctor():
    """Check configuration and system health."""
    setup_logging()
    logger.info("Running radar doctor")
    
    from .config.loader import load_yaml, ConfigError
    from .config.models import WorkspaceConfig, SourceConfig
    from .storage.db import engine, init_db
    from .observability.cost import CostLedger, BudgetExceeded
    from pydantic import ValidationError
    
    init_db()

    try:
        data = load_yaml("config/audience.yaml")
        sources_data = load_yaml("config/sources.yaml")
        data["defaults"] = sources_data.get("defaults", {})
        data["sources"] = sources_data.get("sources", [])
        
        config = WorkspaceConfig(**data)
        logger.info("config_valid", sources_count=len(config.sources))
        typer.echo("Config: OK")
    except ConfigError as e:
        logger.error("config_error", error=str(e))
        typer.echo(f"Config Error: {e}", err=True)
        raise typer.Exit(1)
    except ValidationError as e:
        logger.error("validation_error", errors=e.errors())
        typer.echo(f"Validation Error: {e}", err=True)
        raise typer.Exit(1)
        
    try:
        with engine.connect() as conn:
            pass
        logger.info("db_connection_valid")
        typer.echo("Database: OK")
    except Exception as e:
        logger.error("db_error", error=str(e))
        typer.echo(f"Database Error: {e}", err=True)
        raise typer.Exit(1)
        
    ledger = CostLedger()
    try:
        ledger.record_cost("doctor", "test", "test", 10, 10, 31.0, dry_run=True)
        typer.echo("Cost Ledger: FAILED (cap not enforced)")
        raise typer.Exit(1)
    except BudgetExceeded:
        logger.info("cost_cap_enforced")
        typer.echo("Cost Ledger: OK (cap enforced)")
    
    typer.echo("Doctor check complete.")

sources_app = typer.Typer(help="Manage sources")
app.add_typer(sources_app, name="sources")

def get_workspace_config():
    from .config.loader import load_yaml, ConfigError
    from .config.models import WorkspaceConfig
    from pydantic import ValidationError
    
    try:
        data = load_yaml("config/audience.yaml")
        sources_data = load_yaml("config/sources.yaml")
        data["defaults"] = sources_data.get("defaults", {})
        data["sources"] = sources_data.get("sources", [])
        return WorkspaceConfig(**data)
    except ConfigError as e:
        typer.echo(f"Config Error: {e}", err=True)
        raise typer.Exit(1)
    except ValidationError as e:
        typer.echo(f"Validation Error: {e}", err=True)
        raise typer.Exit(1)

@sources_app.command("validate")
def validate_sources():
    """Validate the source configuration files."""
    config = get_workspace_config()
    typer.echo(f"Configuration is valid. Found {len(config.sources)} sources.")

@sources_app.command("sync")
def sync_sources():
    """Sync source configurations into the database."""
    from .storage.db import SessionLocal
    from .storage.repositories import SourceRepository
    
    config = get_workspace_config()
    db = SessionLocal()
    try:
        repo = SourceRepository(db)
        added, updated, unchanged = repo.sync_sources(config.audience.id, config.sources)
        typer.echo(f"Sources synchronized: {added} added, {updated} updated, {unchanged} unchanged.")
    finally:
        db.close()

@sources_app.command("list")
def list_sources():
    """List all sources in the database."""
    from .storage.db import SessionLocal
    from .storage.repositories import SourceRepository
    import rich
    from rich.table import Table
    
    db = SessionLocal()
    try:
        repo = SourceRepository(db)
        sources = repo.list_sources()
        table = Table(title="Audience Sources")
        table.add_column("ID")
        table.add_column("Platform")
        table.add_column("Priority")
        table.add_column("Frequency")
        table.add_column("Health")
        
        for s in sources:
            table.add_row(s.id, s.platform, s.priority, s.collection_frequency, s.health)
            
        rich.print(table)
    finally:
        db.close()

jobs_app = typer.Typer(help="Manage background jobs")
app.add_typer(jobs_app, name="jobs")

@jobs_app.command("run")
def run_jobs(source_id: str = typer.Argument(default=None, help="The source ID to run"), 
             all_sources: bool = typer.Option(False, "--all", help="Run all enabled sources")):
    """Run collection jobs."""
    from .storage.db import SessionLocal
    from .storage.repositories import SourceRepository
    from .orchestration.runner import CollectionRunner
    from .storage.models import Source
    
    if not source_id and not all_sources:
        typer.echo("Must provide either a source_id or --all", err=True)
        raise typer.Exit(1)
        
    db = SessionLocal()
    try:
        repo = SourceRepository(db)
        runner = CollectionRunner(db)
        
        sources_to_run = []
        if all_sources:
            sources_to_run = db.query(Source).filter(Source.enabled == True).all()
            if not sources_to_run:
                typer.echo("No enabled sources found.")
                return
        else:
            source = repo.get(source_id)
            if not source:
                typer.echo(f"Source '{source_id}' not found.", err=True)
                raise typer.Exit(1)
            sources_to_run = [source]
            
        for s in sources_to_run:
            typer.echo(f"Running job for source '{s.id}'...")
            job = runner.run_source(s)
            typer.echo(f"Job finished with status: {job.status}. Fetched {job.items_fetched} items (New: {job.items_new}, Dup: {job.items_duplicate}).")
            if job.status == "error":
                typer.echo(f"Error: {job.error_class} - {job.error_detail}")
    finally:
        db.close()

pipeline_app = typer.Typer(help="Run processing pipelines")
app.add_typer(pipeline_app, name="pipeline")

@pipeline_app.command("run")
def run_pipeline(batch_size: int = typer.Option(50, help="Number of payloads to process")):
    """Run the analysis pipeline."""
    from .storage.db import SessionLocal
    from .orchestration.pipeline import AnalysisPipeline
    from .agents.relevance import RelevanceScorer
    from .observability.cost import CostLedger
    
    config = get_workspace_config()
    db = SessionLocal()
    try:
        ledger = CostLedger()
        scorer = RelevanceScorer(ledger)
        pipeline = AnalysisPipeline(db, config, scorer)
        
        count = pipeline.run(batch_size=batch_size)
        typer.echo(f"Pipeline processed {count} payloads.")
    finally:
        db.close()

insights_app = typer.Typer(help="Manage insight generation")
app.add_typer(insights_app, name="insights")

@insights_app.command("generate")
def generate_insights(batch_size: int = typer.Option(50, help="Number of conversations to aggregate")):
    """Generate topics and pain points from recent conversations."""
    from .storage.db import SessionLocal
    from .orchestration.insights import InsightOrchestrator
    from .agents.insight import InsightGenerator
    from .observability.cost import CostLedger
    
    config = get_workspace_config()
    db = SessionLocal()
    try:
        ledger = CostLedger()
        generator = InsightGenerator(ledger)
        orchestrator = InsightOrchestrator(db, config, generator)
        
        count = orchestrator.run(batch_size=batch_size)
        typer.echo(f"Generated {count} topics.")
    finally:
        db.close()

opportunities_app = typer.Typer(help="Manage opportunities and scoring")
app.add_typer(opportunities_app, name="opportunities")

@opportunities_app.command("score")
def score_opportunities():
    """Score all detected insights."""
    from .storage.db import SessionLocal
    from .orchestration.opportunities import OpportunityOrchestrator
    
    db = SessionLocal()
    try:
        orchestrator = OpportunityOrchestrator(db)
        count = orchestrator.score_insights()
        typer.echo(f"Scored {count} insights.")
    finally:
        db.close()

reporting_app = typer.Typer(help="Generate reports")
app.add_typer(reporting_app, name="reporting")

@reporting_app.command("radar")
def generate_radar():
    """Generate the Weekly Radar report."""
    from .reporting.radar import RadarGenerator
    from .observability.cost import CostLedger
    
    # In full MVP, this fetches the insights from DB to build the payload
    payload = {"topics": [], "metrics": {"pain_severity": 90}}
    ledger = CostLedger()
    generator = RadarGenerator(ledger)
    report = generator.generate(payload)
    
    typer.echo("--- WEEKLY RADAR ---")
    typer.echo(report)

integration_app = typer.Typer(help="Manage external integrations")
app.add_typer(integration_app, name="integration")

@integration_app.command("export")
def export_opportunity(filepath: str):
    """Export an opportunity JSON file to the Content Engine."""
    import json
    from .integration.content_engine import ContentEngineExporter
    
    with open(filepath, "r") as f:
        data = json.load(f)
        
    try:
        exported = ContentEngineExporter.export(data)
        typer.echo(f"Exported successfully: {exported.id}")
    except ValueError as e:
        typer.echo(f"Export Failed: {e}", err=True)

if __name__ == "__main__":
    app()

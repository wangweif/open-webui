"""Peewee migrations -- 019_add_page_views.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    # Create PageView table for detailed page access logs
    @migrator.create_model
    class PageView(pw.Model):
        id = pw.AutoField()
        url = pw.CharField(max_length=500)
        user_id = pw.CharField(null=True)
        ip_address = pw.CharField(max_length=45)  # Support IPv6
        user_agent = pw.TextField(null=True)
        referer = pw.TextField(null=True)
        access_type = pw.CharField(max_length=50, null=True)  # 访问类型
        created_at = pw.BigIntegerField()
        
        class Meta:
            table_name = "page_view"
    
    # Create PageViewStats table for aggregated statistics
    @migrator.create_model
    class PageViewStats(pw.Model):
        id = pw.AutoField()
        url = pw.CharField(max_length=500, unique=True)
        view_count = pw.IntegerField(default=0)
        first_view_at = pw.BigIntegerField()
        last_view_at = pw.BigIntegerField()
        updated_at = pw.BigIntegerField()
        
        class Meta:
            table_name = "page_view_stats"
    
    # Add indexes for better query performance
    migrator.add_index("page_view", "url")
    migrator.add_index("page_view", "created_at")
    migrator.add_index("page_view", "url", "created_at")
    migrator.add_index("page_view", "access_type")
    migrator.add_index("page_view", "access_type", "created_at")
    migrator.add_index("page_view_stats", "url")
    migrator.add_index("page_view_stats", "view_count")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    # Drop indexes first
    migrator.drop_index("page_view", "url")
    migrator.drop_index("page_view", "created_at") 
    migrator.drop_index("page_view", "url", "created_at")
    migrator.drop_index("page_view", "access_type")
    migrator.drop_index("page_view", "access_type", "created_at")
    migrator.drop_index("page_view_stats", "url")
    migrator.drop_index("page_view_stats", "view_count")
    
    # Remove tables
    migrator.remove_model("page_view")
    migrator.remove_model("page_view_stats")
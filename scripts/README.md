# Database Seeding Scripts

This directory contains scripts for seeding the cycling GPX database with test data.

## Files

- `database_seeding.py` - Main seeding script that generates 1,000 realistic 5km cycling GPX segments across France
- `test_seeding.py` - Test script that generates 5 segments for testing purposes
- `README.md` - This documentation file

## Features

The seeding script generates realistic cycling segments with:

- **Geographic Distribution**: Segments distributed across 13 French regions
- **Realistic Routes**: 5km cycling routes with elevation changes and realistic GPS point distribution
- **Varied Surface Types**: Different surface types (paved roads, trails, etc.) with realistic probabilities
- **Tire Recommendations**: Appropriate tire types for dry and wet conditions
- **Difficulty Levels**: 1-5 difficulty scale
- **Batch Processing**: Processes segments in batches for memory efficiency
- **Storage Integration**: Uploads GPX files to configured storage (local or S3)
- **Database Integration**: Stores segment metadata in PostgreSQL

## Usage

### Prerequisites

1. Ensure your database and storage are configured in `.env/database` and `.env/storage` files
2. Make sure the database is running and accessible
3. Activate the pixi environment: `pixi shell`

### Running the Full Seeding (1,000 segments)

```bash
# From the project root
pixi run python scripts/database_seeding.py
```

### Running the Test Seeding (5 segments)

```bash
# From the project root
pixi run python scripts/test_seeding.py
```

### Customizing the Seeding

You can modify the parameters in the `main()` function of `database_seeding.py`:

```python
await seed_database(
    num_segments=1000,      # Number of segments to generate
    target_distance_km=5.0, # Distance of each segment in km
    batch_size=50           # Number of segments per batch
)
```

## Generated Data

Each generated segment includes:

- **GPX File**: Valid GPX format with realistic GPS points
- **Metadata**: Name, region, surface type, difficulty, tire recommendations
- **Geographic Bounds**: Bounding box for efficient map queries
- **Storage Path**: Reference to the stored GPX file
- **Comments**: Descriptive text about the segment

## French Regions Covered

The script generates segments across these French regions:

1. Île-de-France (Paris region)
2. Provence-Alpes-Côte d'Azur
3. Auvergne-Rhône-Alpes
4. Occitanie
5. Nouvelle-Aquitaine
6. Bretagne
7. Normandie
8. Hauts-de-France
9. Grand Est
10. Bourgogne-Franche-Comté
11. Centre-Val de Loire
12. Pays de la Loire
13. Corse

## Surface Types

Generated segments use these surface types with realistic probabilities:

- Broken Paved Road (30%)
- Dirty Road (20%)
- Field Trail (15%)
- Forest Trail (15%)
- Small Stone Road (10%)
- Big Stone Road (10%)

## Monitoring Progress

The script provides detailed logging including:

- Batch processing progress
- Individual segment generation status
- Storage upload confirmations
- Database commit confirmations
- Error reporting and statistics

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root with `pixi run`
2. **Database Connection**: Verify your database configuration in `.env/database`
3. **Storage Issues**: Check your storage configuration in `.env/storage`
4. **Memory Issues**: Reduce `batch_size` if you encounter memory problems

### Logs

The script logs all activities to stdout. Look for:
- `INFO` messages for normal progress
- `ERROR` messages for failures
- Final statistics showing total processed segments and errors

## Performance

- **Processing Time**: ~2-5 minutes for 1,000 segments (depending on storage type)
- **Memory Usage**: Low memory footprint due to batch processing
- **Storage Space**: ~50-100MB for 1,000 segments (depending on GPX complexity)

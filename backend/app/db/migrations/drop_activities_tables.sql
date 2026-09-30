-- Migration: Consolidate sj_activities into unified sj_tracking
-- Safe to run: child table dropped first to respect FK constraint

DROP TABLE IF EXISTS sj_activity_meta;
DROP TABLE IF EXISTS sj_activities;

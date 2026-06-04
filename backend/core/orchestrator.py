import importlib
import pkgutil
import inspect
from typing import List, Type
from .models import FindingSet
from .base_analyzer import BaseAnalyzer
from .processor import Processor

"""
=== ORCHESTRATOR ===
Dynamically discovers and loads analyzers from the plugins directory.
Coordinates the execution of all registered analyzers.
"""

class Orchestrator:
    def __init__(self):
        self.analyzer_classes: List[Type[BaseAnalyzer]] = []
        self.processor = Processor()
        self._discover_plugins()

    def _discover_plugins(self):
        """
        Dynamically discover analyzer classes in the backend.plugins package.
        """
        print("[Orchestrator] Discovering plugins...")
        import backend.plugins as plugins
        
        # Iterate over modules in the plugins package
        for loader, module_name, is_pkg in pkgutil.iter_modules(plugins.__path__):
            full_module_name = f"backend.plugins.{module_name}"
            module = importlib.import_module(full_module_name)
            
            # Find all classes in the module that inherit from BaseAnalyzer
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAnalyzer) and obj is not BaseAnalyzer:
                    print(f"[Orchestrator] Found analyzer: {obj.__name__}")
                    self.analyzer_classes.append(obj)
        
        print(f"[Orchestrator] Total plugins loaded: {len(self.analyzer_classes)}")


    def run_analysis(self, file_path: str) -> FindingSet:
        """
        Coordinates the execution of all discovered analyzers on a single file.
        Returns a single, aggregated FindingSet.
        """
        all_results = []
        print(f"\n[Orchestrator] Starting analysis on: {file_path}")
        
        # Instantiate and run each discovered analyzer
        for analyzer_class in self.analyzer_classes:
            analyzer_instance = analyzer_class(file_path)
            print(f"[Orchestrator] Running {analyzer_instance.__class__.__name__}...")
            
            try:
                result = analyzer_instance.run()
                all_results.append(result)
            except Exception as e:
                print(f"[Orchestrator] Error running {analyzer_instance.__class__.__name__}: {e}")
                # Create a finding set with error metadata if it fails
                all_results.append(FindingSet(
                    target_file=file_path,
                    metadata={"error": str(e), "tool": analyzer_instance.__class__.__name__}
                ))
            
        print(f"[Orchestrator] Analysis Complete. Collected {len(all_results)} result set(s).")
        
        # New Step: Process results (Normalization, Deduplication, Scoring)
        final_report = self.processor.process_results(file_path, all_results)
        return final_report

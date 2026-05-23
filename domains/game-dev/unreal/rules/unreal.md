# Unreal Engine Development Rules

Rules for AI-assisted Unreal Engine development with C++ and Blueprints. Follow these in every Unreal project.

## Project Structure

- Follow Unreal's module-based architecture: each logical system lives in its own module with a `Public/` and `Private/` directory.
- Keep the `Source/` directory clean: one directory per module, with a `.Build.cs` file at the root.
- Separate gameplay code from engine extensions; gameplay modules belong in `Source/<ProjectName>/`, engine/editor extensions in `Source/<ModuleName>/`.
- Use the Unreal Header Tool (UHT) macros (`UCLASS`, `USTRUCT`, `UPROPERTY`, `UFUNCTION`) correctly; UHT generates reflection data from these.
- Configure module dependencies explicitly in `.Build.cs` files; avoid circular dependencies between modules.

## C++ Coding Conventions

- Prefix all Unreal types: `U` for `UObject`-derived classes, `A` for `AActor`-derived, `F` for structs and plain data types, `I` for interfaces, `E` for enums, `T` for templates.
- Always mark `UFUNCTION` and `UPROPERTY` with appropriate specifiers (`BlueprintCallable`, `BlueprintReadOnly`, `EditAnywhere`, `Category`, `meta`).
- Use `TArray` instead of `std::vector`, `TMap` instead of `std::unordered_map`, `FString` instead of `std::string`, `TSharedPtr`/`TUniquePtr` instead of `std::shared_ptr`/`std::unique_ptr`.
- Declare overrides with the `override` keyword; Unreal's `virtual` functions should always be overridden through the engine's macro system.
- Use `check()`, `ensure()`, and `verify()` macros for assertions — never use raw `assert()`.
- Avoid `Tick()` when possible; prefer timers, delegates, or event-driven updates.
- Use `UPROPERTY()` with `Transient`, `SkipSerialization`, or `DuplicatesTransient` specifiers to control save/load/duplication behaviour.

## API Usage Patterns

- Use the Gameplay Ability System (GAS) for complex gameplay mechanics: Attributes, GameplayEffects, GameplayAbilities, GameplayTags.
- Favor `Enhanced Input` over the legacy input system; use `InputAction` assets and `InputMappingContext`.
- Use `FSoftObjectPath` and `FStreamableManager` for asynchronous asset loading; never use synchronous `LoadObject` in shipping builds.
- Prefer `TSubclassOf<T>` for class references in `UPROPERTY` fields instead of raw `UClass*` pointers.
- Use `GetWorld()->GetTimerManager()` for time-based callbacks; never spin-wait or use `FPlatformProcess::Sleep()` for gameplay timing.
- Use `FDelegateHandle` to manage delegate subscriptions and always unregister in `EndPlay()` or the destructor.
- Batch gameplay queries with `UWorld::OverlapMultiByChannel()` or `OverlapMultiByObjectType()` instead of per-frame `GetAllActorsOfClass()`.

## Performance

- Profile with `Unreal Insights` and `stat` console commands before optimizing; target specific bottlenecks identified by the profiler.
- Avoid `Cast<T>()` in hot paths; use `IsA()` checks or cached weak pointers when the type is known ahead of time.
- Use object pooling via `UObjectPool` or custom managers for frequently spawned/destroyed actors.
- Minimize dynamic memory allocation in `Tick()`; pre-allocate `TArray` with `Reserve()` when the expected size is known.
- Mark functions as `FORCEINLINE` only when profiling proves it beneficial; trust the compiler's inlining heuristics.
- Use `UPrimitiveComponent` LOD and culling settings to reduce draw calls — configure `bNeverDistanceCull` only when necessary.
- Leverage the `ParallelFor` API on `FQueuedThreadPool` for data-parallel operations; never spawn raw threads manually.

## Common Pitfalls

- Garbage Collection: `UObject` pointers must be marked with `UPROPERTY()` or added to `FGCObjectScopeGuard` to prevent premature GC; raw `UObject*` in non-UPROPERTY fields are GC-unsafe.
- Never call `BeginPlay()`, `Tick()`, or `EndPlay()` manually — these are engine lifecycle hooks called by the world.
- `UObject::CreateDefaultSubobject()` must only be called from a constructor; calling it at runtime produces undefined behaviour.
- Blueprint-exposed functions need `UFUNCTION(BlueprintCallable)`; without it, Blueprints cannot call them.
- Network replication: only server-authoritative actors call `SetReplicates(true)`; use `GetLifetimeReplicatedProps()` to register replicated properties.
- `AActor::Destroy()` is deferred to the end of the frame; do not rely on immediate destruction in the same frame.
- Never store raw `AActor*` pointers that could be garbage collected; use `TWeakObjectPtr<>` or check with `IsValid()` before every access.

## Testing

- Use the Unreal Automation Framework with `IMPLEMENT_SIMPLE_AUTOMATION_TEST` or `IMPLEMENT_COMPLEX_AUTOMATION_TEST`.
- Write functional tests with `AFunctionalTest` actors and Gauntlet for integration testing.
- Mock dependencies with Unreal's `FAutomationTestBase` and the spec test macros (`Describe`, `It`, `TestEqual`).
- Run the `Session Frontend` > `Automation` panel to execute tests in-editor; run command-line tests via `-ExecCmds="Automation RunTests"`.

## Editor Tooling

- Extend the editor with `UEditorUtilityWidget`, `FWorkspaceItem`, and `FExtender` for custom tool windows and menu extensions.
- Use `FSlateApplication` and `SWidget` classes for Slate-based editor UI; avoid UMG widgets for editor tools.
- Register asset type actions with `IAssetTypeActions` and `UFactory` derived classes for custom asset creation pipelines.
- Use `FPropertyEditorModule` and `IDetailCustomization` to customize the Details panel for your custom types.
- Preference editor extensions over asset manipulation; always use `FScopedTransaction` for undo/redo support.

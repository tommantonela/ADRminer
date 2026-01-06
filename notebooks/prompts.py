
# -------------------------------------------------------------------------------------------------

KRUCHTEN_FRAMEWORK_V1 = """Your task is to analyze Architectural Decision Records (ADRs) to identify architectural decisions types according to Philippe Kruchten’s ontology of architectural decisions in software-intensive systems. 
Use the definitions provided below, derived from Kruchten’s ontology of architectural decisions in software-intensive systems.

## Categories:
* Existence (ontocrisis): This decision declares that an element or artifact *will exist* in the design or implementation. Includes structural decisions (e.g., layers, components) and behavioral decisions (e.g., connectors, interactions). Structural decisions lead to the creation of subsystems, layers, partitions, components in some view of the architecture. Behavioural decisions are more related to how the elements interact together to provide functionality or to satisfy some non functional requirement (quality attribute), or connectors.
* Ban/Non-Existence (anticrisis): This decision declares that an element *will not exist* in the design or implementation. Often used to rule out alternatives.
* Property (diacrisis): This decision states a general, enduring quality or constraint of the system. These are often cross-cutting concerns or design rules (positive) or constraints (negative).
* Executive (pericrisis): This refers to a decision that does not relate directly to the design elements or their qualities, but is driven more by the business environment (financial), and affect the development process (methodological), the people (education and training), the organization, and to a large extend the choices of technologies and tools.

If the ADR does not clearly fit any of the defined architectural decision types, select:
* Other / Unclassified: The ADR does not conform to any of the known categories (e.g., existence, non-existence, property, executive), or the type is ambiguous or not evident from the text.

## Guidelines:
* Use all information available, base your classification on what is available, noting uncertainty if needed.
* If uncertain about classification, assign the most likely category and reflect that uncertainty in your confidence scores.
* Always explain your reasoning briefly but clearly.
""" 

KRUCHTEN_FRAMEWORK_WITH_EXAMPLES_V1 = """Your task is to analyze Architectural Decision Records (ADRs) to identify architectural decisions types according to Philippe Kruchten’s ontology of architectural decisions in software-intensive systems. 
Use the definitions provided below, derived from Kruchten’s ontology of architectural decisions in software-intensive systems.

## Categories:
* Existence (ontocrisis): It declares that an element or artifact *will exist* in the design or implementation. Includes structural decisions (e.g., layers, components) and behavioral decisions (e.g., connectors, interactions). Structural decisions lead to the creation of subsystems, layers, partitions, components in some view of the architecture. Behavioural decisions are more related to how the elements interact together to provide functionality or to satisfy some non functional requirement (quality attribute), or connectors.
    - E.g., "The logical view is organized in 3 layers: Data, Business Logic, UI."
    - E.g., "Communication between classes uses RMI."
* Ban/Non-Existence (anticrisis): It declares that an element *will not exist* in the design or implementation. Often used to rule out alternatives.
    - E.g., "The system does not use MySQL as its relational database."
    - E.g., "The system does not reuse the flight management system from project ASIEW."
* Property (diacrisis): It states a general, enduring quality or constraint of the system. These are often cross-cutting concerns or design rules (positive) or constraints (negative).
    - E.g., "All domain-related classes are defined in Layer #2."
    - E.g., "No use of open-source components that restrict closed redistribution."
* Executive (pericrisis): It refers to decisions that do not relate directly to the design elements or their qualities, but are driven more by the business environment (financial), and affect the development process (methodological), the people (education and training), the organization, and to a large extend the choices of technologies and tools.
    - E.g., "All API changes must be approved by the Change Control Board."
    - E.g., "The system will be built in Java using J2EE and System Architect Workbench."

If the ADR does not clearly fit any of the defined architectural decision types, select:
* Other / Unclassified: The ADR does not conform to any of the known categories (e.g., existence, non-existence, property, executive), or the type is ambiguous or not evident from the text.

## Guidelines:
* Use all information available, base your classification on what is available, noting uncertainty if needed.
* If uncertain about classification, assign the most likely category and reflect that uncertainty in your confidence scores.
* Always explain your reasoning briefly but clearly.
"""

KRUCHTEN_FRAMEWORK_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one and only one category. 
Use the category definitions, guidelines and rules provided below, which are derived from Kruchten’s ontology of architectural decisions in software-intensive systems.

## Categories:
- **Existence (ontocrisis)**: This decision declares that an *element or artifact will exist* in the design or implementation. Includes structural decisions (e.g., layers, components) and behavioral decisions (e.g., connectors, interactions). Structural decisions lead to the creation of subsystems, layers, partitions, components in some view of the architecture. Behavioural decisions are more related to how the elements interact together to provide functionality or to satisfy some non functional requirement (quality attribute), or connectors.
- **Ban/Non-Existence (anticrisis)**: This decision declares that an *element will not exist* in the design or implementation. Often used to rule out alternatives.
- **Property (diacrisis)**: This decision states a *general, enduring quality or constraint* of the system. These are often cross-cutting concerns or design rules (positive) or constraints (negative).
- **Executive (pericrisis)**: This refers to a decision that does not relate directly to the design elements or their qualities, but is *driven by the business environment* (financial), and *affect the development process* (methodological), the *people* (education and training), and the *organization*.

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- In your analysis, first identify the core subject of the decision and then map it to the corresponding category: 
    + is it about creating/choosing a software element for the system to be built? -> Existence 
    + is it about forbidding a software element of the system? -> Ban/Non-Existence 
    + is it setting a rule about system behavior/structure or a quality? -> Property 
    + is it about dictating a process/context for developing the system? -> Executive
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If uncertain because more than one category seems suitable, choose the most likely category and reflect that uncertainty in your confidence scores and alternative categories.
-- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Tests:
- For identifying an **Existence** decision: 
    + does this *create* or *select* a specific architectural element of the system?
- For identifying an **Executive decision**:
    + does this govern *how we work* rather than *what we build*?
    + is this about our *development process or methodology*?"

## Disambiguation Rules: Apply these when multiple tests seem equally valid for the ADR
- **Existence versus Executive**: An Existence decision becomes part of the running system to be built during the project, 
while an Executive decision pertains to the proces to develop/manage a system (but it is NOT part of the running system to be built)
- On *tool selection*:
    + if the tool becomes *part of the system* -> Existence
    + if the tool is for *development* or for a *process* -> Executive

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
""" 

KRUCHTEN_FRAMEWORK_WITH_EXAMPLES_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one and only one category. 
Use the category definitions, guidelines, rules and examples provided below, which are derived from Kruchten’s ontology of architectural decisions in software-intensive systems.

## Categories:
- **Existence (ontocrisis)**: This decision declares that an *element or artifact will exist* in the design or implementation. Includes structural decisions (e.g., layers, components) and behavioral decisions (e.g., connectors, interactions). Structural decisions lead to the creation of subsystems, layers, partitions, components in some view of the architecture. Behavioural decisions are more related to how the elements interact together to provide functionality or to satisfy some non functional requirement (quality attribute), or connectors.
Examples:
    + ✅ "We will use PostgreSQL as our primary database"
    + ✅ "Implement an API Gateway for routing"
    + ✅ "Adopt GraphQL for data querying"
    + ❌ "All databases must have replication" (This is a Property - it's a rule about the system)
- **Ban/Non-Existence (anticrisis)**: This decision declares that an *element will not exist* in the design or implementation. Often used to rule out alternatives.
Examples:
    + ✅ "Do not use MongoDB for transaction processing"
    + ✅ "Avoid synchronous communication between services"
    + ✅ "No stored procedures in the database"
    + ❌ "No service may exceed 500ms response time" (This is a Property - it's a performance rule)
- **Property (diacrisis)**: This decision states a *general, enduring quality or constraint* of the system. These are often cross-cutting concerns or design rules (positive) or constraints (negative).
Examples:
    + ✅ "All microservices must have health check endpoints"
    + ✅ "Data must be encrypted at rest and in transit"
    + ✅ "APIs must implement rate limiting"
    + ❌ "Use encryption libraries from the approved vendor list" (This is Executive - tool/process choice)
- **Executive (pericrisis)**: This refers to a decision that does not relate directly to the design elements or their qualities, but is *driven by the business environment* (financial), and *affect the development process* (methodological), the *people* (education and training), and the *organization*.
Examples:
    + ✅ "The team will practice Test-Driven Development"
    + ✅ "All PRs require two approvals before merging"
    + ✅ "Use AWS as our cloud provider" (Note: This is Executive because it's a procurement/business decision)
    + ❌ "All data must be stored in S3 buckets" (This is Property - system structure rule)

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- In your analysis, first identify the core subject of the decision and then map it to the corresponding category: 
    + is it about creating/choosing a software element for the system to be built? -> Existence 
    + is it about forbidding a software element of the system? -> Ban/Non-Existence 
    + is it setting a rule about system behavior/structure or a quality? -> Property 
    + is it about dictating a process/context for developing the system? -> Executive
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If uncertain because more than one category seems suitable, choose the most likely category and reflect that uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Tests:
- For identifying an **Existence** decision: 
    + does this *create* or *select* a specific architectural element of the system?
- For identifying an **Executive decision**:
    + does this govern *how we work* rather than *what we build*?
    + is this about our *development process or methodology*?"

## Disambiguation Rules: Apply these when multiple tests seem equally valid for the ADR
- **Existence versus Executive**: An Existence decision becomes part of the running system to be built during the project, 
while an Executive decision pertains to the proces to develop/manage a system (but it is NOT part of the running system to be built)
- On *technology choices*, CONTEXT matters:
    + e.g., "Use Docker for deployment" -> Existente (creates deployment architecture)
    + e.g., "Use Docker for local development" -> Executive (development tooling)
    + e.g., "All containers must be immutable" -> Property (system rule)
- On *security*:
    + e.g., "Data must be encrypted" -> Property (system constraint)
    + e.g., "Use OAuth 2.0 for authentication" -> Existence (creates element)
    + e.g., "Conduct penetration testing quarterly" -> Executive (process)
- On *tool selection*:
    + if the tool becomes *part of the system* being constructed -> Existence, e.g, "Use Kafka for event streaming"
    + if the tool is for *development* or for a *process* -> Executive, e.g., "Use GitHub Actions for CI/CD"

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
""" 

# -------------------------------------------------------------------------------------------------

QUALITY_ATTRIBUTES_FRAMEWORK_V1 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one primary category. 
The categories refer to referenced or implied quality attributes (non-functional requirements). 
Use the category definitions and guidelines provided below, derived from ISO/IEC 25010 and the Bass/Clements/Kazman (Software Engineering Institute) framework for quality attributes.

## Categories:
- Performance: The degree to which a system performs its functions within specified time and throughput parameters, efficiently utilizing resources such as CPU, memory, and storage. 
- Reliability: The degree to which a system performs specified functions under stated conditions for a specified period, encompassing attributes like fault tolerance and recoverability. 
- Security: The degree to which a system protects information and data to ensure appropriate access and prevent unauthorized access or modifications. 
- Maintainability: The degree of effectiveness and efficiency with which a system can be modified, including aspects like modularity, reusability, and testability. 
- Scalability: The capability of a system to handle increased load by expanding resources, often through horizontal scaling.
- Usability: The degree to which a system can be used by specified users to achieve specified goals with effectiveness, efficiency, and satisfaction in a specified context of use. 
- Portability: The degree of effectiveness and efficiency with which a system can be transferred from one environment to another, including adaptability and installability. 
- Compatibility: The degree to which a system can exchange information with other systems and perform its required functions while sharing the same environment. 
- Observability: The degree to which a system's internal states can be inferred from its external outputs, facilitating monitoring and debugging.
- Testability: The degree of effectiveness and efficiency with which test criteria can be established for a system and tests can be performed to determine whether those criteria have been met. 

If no quality attribute is mentioned or implied, select:
- Only Functional Concern: The ADR describes only what the system must do, and not so much how well the system should do it, it has no qualit-attribute connotations.

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- While more than one attribute may be related to an ADR, choose the category that is the primary focus or direct driver of the decision described in the ADR.
- If uncertain because more than one category seems suitable, choose the most likely category and reflect that uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories.
"""

QUALITY_ATTRIBUTES_FRAMEWORK_WITH_EXAMPLES_V1 = """
Your task is to analyze Architectural Decision Records (ADRs) to identify referenced or implied quality attributes (non-functional requirements). 
Use the definitions provided below, derived from ISO/IEC 25010 and the Bass/Clements/Kazman (Software Engineering Institute) framework for quality attributes.

## Categories:
* Performance: The degree to which a system performs its functions within specified time and throughput parameters, efficiently utilizing resources such as CPU, memory, and storage.
    - E.g., response time, throughput, resource usage. 
* Reliability: The degree to which a system performs specified functions under stated conditions for a specified period, encompassing attributes like fault tolerance and recoverability.
    - E.g., fault tolerance, recovery from failure. 
* Security: The degree to which a system protects information and data to ensure appropriate access and prevent unauthorized access or modifications. 
    - E.g., confidentiality, integrity, access control. 
* Maintainability: The degree of effectiveness and efficiency with which a system can be modified, including aspects like modularity, reusability, and testability. 
    - E.g., modularity, readability, guideline compliance. 
* Scalability: The capability of a system to handle increased load by expanding resources, often through horizontal scaling.
    - E.g., support for growing loads, horizontal scaling.
* Usability: The degree to which a system can be used by specified users to achieve specified goals with effectiveness, efficiency, and satisfaction in a specified context of use.
    - E.g., accessibility, user experience, interface quality. 
* Portability: The degree of effectiveness and efficiency with which a system can be transferred from one environment to another, including adaptability and installability.
    - E.g., platform independence, environment neutrality. 
* Compatibility: The degree to which a system can exchange information with other systems and perform its required functions while sharing the same environment.
    - E.g., API/version compatibility, system interop. 
* Observability: The degree to which a system's internal states can be inferred from its external outputs, facilitating monitoring and debugging.
    - E.g., metrics, logging, tracing.
* Testability: The degree of effectiveness and efficiency with which test criteria can be established for a system and tests can be performed to determine whether those criteria have been met. 
    - E.g., test hooks, mocking support, test coverage. 

If no quality attribute is mentioned or implied, select:
* Only Functional Concern: The ADR solely describes functional aspects (e.g., what the system does), without reference to how well it should do them (performance, security, scalability, etc.).

## Guidelines:
* Use all information available, base your classification on what is available, noting uncertainty if needed.
* If uncertain about classification, assign the most likely category and reflect that uncertainty in your confidence scores.
* Always explain your reasoning briefly but clearly.
"""

QUALITY_ATTRIBUTES_FRAMEWORK_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one primary category. 
The categories refer to referenced or implied quality attributes (non-functional requirements) of a system. 
Use the category definitions, guidelines and rules provided below, derived from ISO/IEC 25010 and the Bass/Clements/Kazman (Software Engineering Institute) framework for quality attributes.
Keep in mind that the quality attributes should refer to the *system being built* rather than to the *process or environment to develop the system*.

## Categories:
- **Performance**: The degree to which a system performs its functions within specified time and throughput parameters, efficiently utilizing resources such as CPU, memory, and storage. 
- **Reliability**: The degree to which a system performs specified functions under stated conditions for a specified period, encompassing attributes like fault tolerance and recoverability. 
- **Security**: The degree to which a system protects information and data to ensure appropriate access and prevent unauthorized access or modifications. 
- **Maintainability**: The degree of effectiveness and efficiency with which a system can be modified, including aspects like modularity, reusability, and testability. 
- **Scalability**: The capability of a system to handle increased load by expanding resources, often through horizontal scaling.
- **Usability**: The degree to which a system can be used by specified users to achieve specified goals with effectiveness, efficiency, and satisfaction in a specified context of use. 
- **Portability**: The degree of effectiveness and efficiency with which a system can be transferred from one environment to another, including adaptability and installability. 
- **Compatibility**: The degree to which a system can exchange information with other systems and perform its required functions while sharing the same environment. 
- **Observability**: The degree to which a system's internal states can be inferred from its external outputs, facilitating monitoring and debugging.
- **Testability**: The degree of effectiveness and efficiency with which test criteria can be established for a system and tests can be performed to determine whether those criteria have been met. 

If no quality attribute is mentioned or implied, select:
- **Other/Only Functional Concern**: The ADR solely describes functional aspects (e.g., what the system does), without reference to how well it should do them (performance, security, scalability, etc.).
Also include in this category any ADR that describes aspects of the development process or methodology for the system.

## Guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- Be cautious about keywords, as they can provide hints but should be *always interpreted in context*.
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If the ADR mentions sacrificing one atribute for the other (i.e. a tradeoff), classify the ADR based on what is being "gained".
- If uncertain because more than one category seems suitable, choose the most likely category and reflect that uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Disambiguation rules:
- **Other/Only Functional Concern versus Maintainability, or any other quality attribute** above: 
    + Does the ADR discusses *only WHAT the system does*? If there is *NO* mention or clear implication of *HOW WELL, FAST, SECURELY, EASY TO CHANGE or RELIABLY* it should do it, -> Other/Only Functional Concern
    + Aspects of code documentation, code quality, naming conventions, linting, or release management usually DO NOT belong to Maintainability.
- On sub-aspects of **Maintainability**:
    + If the first attempt to classify an ADR is for Maintainability, carefully test for related qualities that in certain contexts can be 
    sub-aspects of Maintainability such as Compatibility, Portability or Testability, and they might be a better fit for the classification.
- **Performance versus Maintainability**:
    + if the ADR describes optimizing an existing implementation (of the system) for speed or efficiency -> Performance
    + if the ADR describes changes to the structure or organization of the systemm for ease of change -> Modifiability
- **Testability versus Maintainability**:  
    + if the ADR focuses specifically on verification, testing or validation -> Testability
    + if the ADR is about ease of change, code organization or developer efficiency -> Maintainability
- **Scalability versus Performance**: 
    + if the ADR addresses growth, capacity planning, or increased load -> Scalability 
    + if the ADR evidences an optimization for time, throughput, resource usage or other constraints -> Performance
- **Observability versus Maintainability**: 
    + if the ADR focuses on runtime monitoring, debugging of issues, or system transparency -> Observability
    + if the ADR focuses on development-time analysis or making the codebase easier to understand -> Maintainability
- **Compatibility versus Portability**:
    + if the ADR focuses on working with other systems, APIs, or versions -> Compatiblity
    + if the ADR focuses on running in different environments or platforms -> Portability
- If *multiple attributes* seem relevant, choose based on the *explicit goal* stated in the ADR and CONTEXT. 

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
"""

QUALITY_ATTRIBUTES_FRAMEWORK_WITH_EXAMPLES_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one primary category. 
The categories refer to referenced or implied quality attributes (non-functional requirements) of a system. 
Use the category definitions, guidelines, rules and examples provided below, derived from ISO/IEC 25010 and the Bass/Clements/Kazman (Software Engineering Institute) framework for quality attributes.
Keep in mind that the quality attributes should refer to the *system being built* rather than to the *process or environment to develop the system*.

## Categories:
- **Performance**: The degree to which a system performs its functions within specified time and throughput parameters, efficiently utilizing resources such as CPU, memory, and storage.
    + e.g., the decision is primarily motivated by response time, throughput, resource usage. 
- **Reliability**: The degree to which a system performs specified functions under stated conditions for a specified period, encompassing attributes like fault tolerance and recoverability.
    + e.g., the decision is primarily motivated by availability, fault tolerance, recovery from failure. 
- **Security**: The degree to which a system protects information and data to ensure appropriate access and prevent unauthorized access or modifications. 
    + e.g., the decision is primarily motivated by confidentiality, integrity, access control, accountability. 
- **Maintainability**: The degree of effectiveness and efficiency with which a system can be modified, including aspects like modularity, reusability, and testability. 
    + e.g., the decision is primarily motivated by modularity, readability, guideline compliance. 
- **Scalability**: The capability of a system to handle increased load by expanding resources, often through horizontal scaling.
    + e.g., the decision is primarily motivated by support for growing loads, horizontal scaling.
- **Usability**: The degree to which a system can be used by specified users to achieve specified goals with effectiveness, efficiency, and satisfaction in a specified context of use.
    + e.g., the decision is primarily motivated by accessibility, user experience, interface quality, operator. 
- **Portability**: The degree of effectiveness and efficiency with which a system can be transferred from one environment to another, including adaptability and installability.
    + e.g., the decision is primarily motivated by platform independence, environment neutrality. 
- **Compatibility**: The degree to which a system can exchange information with other systems and perform its required functions while sharing the same environment.
    + e.g., the decision is primarily motivated by API/version compatibility, system interoperability. 
- **Observability**: The degree to which a system's internal states can be inferred from its external outputs, facilitating monitoring and debugging.
    + e.g., the decision is primarily motivated by metrics, logging, tracing.
- **Testability**: The degree of effectiveness and efficiency with which test criteria can be established for a system and tests can be performed to determine whether those criteria have been met. 
    + e.g., the decision is primarily motivated by test hooks, mocking support, test coverage. 

If no quality attribute is mentioned or implied, select:
- **Other/Only Functional Concern**: The ADR solely describes functional aspects (e.g., what the system does), without reference to how well it should do them (performance, security, scalability, etc.).
Also include in this category any ADR that describes aspects of the development process or methodology for the system.

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- Be cautious about keywords, as they can provide hints but should be *always interpreted in context*.
    + e.g., "scalable" might refer to team scalability (Maintainability) rather than to system scalability (Scalability)
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If the ADR mentions sacrificing one atribute for the other (i.e. a tradeoff), classify the ADR based on what is being "gained".
- If uncertain because more than one category seems suitable, choose the most likely category and reflect that uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Disambiguation rules:
- **Only Functional Concern versus Maintainability, or any other quality attribute** above: 
    + Does the ADR discusses *only WHAT the system does*? If there is *NO* mention or clear implication of *HOW WELL, FAST, SECURELY, EASY TO CHANGE or RELIABLY* it should do it, -> Other/Only Functional Concern
    + Aspects of code documentation, code quality, naming conventions, linting, or release management usually DO NOT belong to Maintainability.
- On sub-aspects of **Maintainability**:
    + If the first attempt to classify an ADR is for Maintainability, carefully test for related qualities that in certain contexts can be 
    sub-aspects of Maintainability such as Compatibility, Portability or Testability, and they might be a better fit for the classification.
- **Performance versus Maintainability**:
    + if the ADR describes optimizing an existing implementation (of the system) for speed or efficiency -> Performance
    + if the ADR describes changes to the structure or organization of the systemm for ease of change -> Modifiability
- **Testability versus Maintainability**:  
    + if the ADR focuses specifically on verification, testing or validation -> Testability
    + if the ADR is about ease of change, code organization or developer efficiency -> Maintainability
    + e.g., "We will use dependency injection to make unit testing easier" -> Testability
- **Scalability versus Performance**: 
    + if the ADR addresses growth, capacity planning, or increased load -> Scalability 
    + if the ADR evidences an optimization for time, throughput, resource usage or other constraints -> Performance
    + e.g., "We will add read replicas to handle anticipated user growth" -> Scalability
- **Observability versus Maintainability**: 
    + if the ADR focuses on runtime monitoring, debugging of issues, or system transparency -> Observability
    + if the ADR focuses on development-time analysis or making the codebase easier to understand -> Maintainability
    + e.g., "We will add structured logging to debug live incidents" -> Observability
- **Compatibility versus Portability**:
    + if the ADR focuses on working with other sysetms, APIs, or versions -> Compatiblity
    + if the ADR focuses on running in different environments or platforms -> Portability
    + e.g., "We will ensure the API maintains backward compatibility" -> Compatibility
- If *multiple attributes* seem relevant, choose based on the *explicit goal* stated in the ADR and CONTEXT. 
    + e.g, "We will add a cache *to improve response times*" -> Performance** (even if it also improves Scalability)
    + e.g. "We will use a message queue *to decouple services and allow independent scaling*" -> Scalability (even if it also improves Reliability) 

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
"""

# -------------------------------------------------------------------------------------------------

ZIMMERMANN_FRAMEWORK_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one primary category. 
Use the category definitions, guidelines and rules provided below.

## Categories:
- **Design**: This decision concerns the logical organization, structure, and decomposition of the system. It is related to patterns, components, layering, interfaces, data modeling.
- **Technology**: This decision concerns the selection of technologies, platforms, frameworks, libraries, or standards.
- **Infrastructure**: This decision involves the deployment environment, hosting, runtime platforms, networking, and hardware concerns.
- **Organizational/Process**: This decision concerns team structures, roles, responsibilities, workflows, and processes that affect architecture.
- **Constraint**: It refers to mandatory conditions from the business, regulations, or existing systems that limit architectural choices.
- **Quality Attribute**: This decision explicitly targets system qualities like performance, security, availability, etc. It primarily addresses a non-functional requirement.
- **Crosscutting Concerns**: This refers to decisions that impact multiple parts of the system simultaneously, often aspects like logging, monitoring, security mechanisms.
- **Implementation**: This decision affects internal code structure, patterns at the class or method level, or maintainability mechanisms, but are not architectural in scope.
- **Other**: Use this only if the decision clearly does not fit any previous category. 

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If uncertain because more than one category seems suitable, use the disambiguation rules (below) and choose the most likely category. Reflect any category uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Disambiguation rules:
- **Quality Attribute versus Crosscutting Concerns**: A decision about a quality attribute can affect several components or elements of the system,
i.e., be crosscutting. The quality attribute must be a GOAL explicitly stated in the ADR and not a side-effect. If so, prioritize the Quality Attribute category, and then note the Crosscutting Concerns as an alternative in your assessment.
- **Design versus Crosscutting Concerns**: A Design decision can affect several components or elements of the system,
i.e., be crosscutting. In this case, prioritize the Design category, and then note the Crosscutting Concerns as an alternative in your assessment.
- **Design versus Technology**: If the Design aspect is more relevant or crosscutting than the actual Technology or tool (which might be substituted for another one), prefer Design.
- **Constraint versus the other categories**: A constraint must be imposed and non-negotiable. If this is the main focus of the ADR, then prioritize the Constraint category.
- **Technology versus Crosscutting Concerns**: 
    + the focus is on platform selection -> Technology
    + the focus is on the fact that it affects all services -> Crosscuting Concerns
- **Infrastructure versus Technology**: 
    + the focus is on platform selection -> Technology
    + the focus is on tool selection for the development platform or process -> Infrastructure
    + the focus is on deployment or orchestration aspects -> Infrastructure
- **Design versus Implementation**: 
    + does it affect component boundaries, intefaces or system decompositions? -> Design
    + does it affect code organization *within* an already-defined component? -> Implementation
- **Organizational/Process versus Constraint":
    + is it a team or process agreement about how to work? -> Organizational/Process
    + is it an imposed rule with no team-related discretion? -> Constraint

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
"""

ZIMMERMANN_FRAMEWORK_WITH_EXAMPLES_V2 = """Your are a senior software architect.
Your task is to analyze a given Architectural Decision Records (ADR) and classify it into one primary category. 
Use the category definitions, guidelines, rules and examples provided below.

## Categories:
- **Design**: This decision concerns the logical organization, structure, and decomposition of the system. It is related to patterns, components, layering, interfaces, data modeling.
  + e.g., "We apply the Model-View-Controller pattern for the UI."
  + e.g., "Services must be stateless to support scalability." (emphasis is more on stateless services than on scalability)
- **Technology**: This decision concerns the selection of technologies, platforms, frameworks, libraries, or standards.
  + e.g., "We use Kubernetes for container orchestration."
  + e.g., "The database must be PostgreSQL 14."
- **Infrastructure**: This decision involves the deployment environment, hosting, runtime platforms, networking, and hardware concerns.
  + e.g., "Production servers must be hosted on AWS EC2 instances."
  + e.g., "Services will communicate over a secured VPN."
- **Organizational/Process**: This decision concerns team structures, roles, responsibilities, workflows, and processes that affect architecture.
  + e.g., "All changes must be approved by the Architecture Review Board."
  + e.g., "Scrum is adopted for project management."
- **Constraint**: It refers to mandatory conditions from the business, regulations, or existing systems that limit architectural choices.
  + e.g., "Compliance with GDPR is required."
  + e.g., "We must reuse the legacy CRM system without modifications."
- **Quality Attribute**: This decision explicitly targets system qualities like performance, security, availability, etc. It primarily addresses a non-functional requirement.
  + e.g., "All APIs must respond within 200ms under normal load."
  + e.g., "System must be highly available with 99.99% uptime."
- **Crosscutting Concerns**: This refers to decisions that impact multiple parts of the system simultaneously, often aspects like logging, monitoring, security mechanisms.
  + e.g., "All services must include structured logging in JSON."
  + e.g., "Authentication must be centralized via OAuth2."
- **Implementation**: This decision affects internal code structure, patterns at the class or method level, or maintainability mechanisms, but are not architectural in scope.
  + e.g., "We implement a Repository pattern class to separate data access from business logic."
  + e.g., "Service classes should use constructor-based dependency injection."
  + e.g., "Each domain object implements a to_dict() method for JSON serialization."
- **Other**: Use this only if the decision clearly does not fit any previous category. 
  + e.g., "This ADR exists only to record that we had a meeting on this topic."
  + e.g., "Decision withdrawn – no action taken."
  + e.g., "We document this placeholder for a future decision."

## Classification guidelines:
- Use all information available, base your classification on what is available, noting uncertainty if needed.
- Look for the primary, governing decision in the ADR, i.e., its core mandate. Use the tests and disambiguation rules (below) in your assessent.
- If uncertain because more than one category seems suitable, use the disambiguation rules (below) and choose the most likely category. Reflect any category uncertainty in your confidence scores and alternative categories.
- Always explain your reasoning briefly but clearly about the identified category, as well as the discarded categories. You can also include tests and disambiguation rules applied.

## Disambiguation rules:
- **Quality Attribute versus Crosscutting Concerns**: A decision about a quality attribute can affect several components or elements of the system,
i.e., be crosscutting. The quality attribute must be a GOAL explicitly stated in the ADR and not a side-effect. If so, prioritize the Quality Attribute category, and then note the Crosscutting Concerns as an alternative in your assessment.
- **Design versus Crosscutting Concerns**: A Design decision can affect several components or elements of the system,
i.e., be crosscutting. In this case, prioritize the Design category, and then note the Crosscutting Concerns as an alternative in your assessment.
- **Design versus Technology**: If the Design aspect is more relevant or crosscutting than the actual Technology or tool (which might be substituted for another one), prefer Design.
- **Constraint versus the other categories**: A constraint must be imposed and non-negotiable. If this is the main focus of the ADR, then prioritize the Constraint category.
- **Technology versus Crosscutting Concerns**: e.g., "We will use Kubernetes"
    + the focus is on platform selection -> Technology
    + the focus is on the fact that it affects all services -> Crosscuting Concerns
- **Infrastructure versus Technology**: e.g., "We will use Kubernetes"
    + the focus is on platform selection for the system to be built -> Technology
    + the focus is on tool selection for the development platform or process -> Infrastructure
    + the focus is on deployment or orchestration aspects -> Infrastructure
- **Design versus Implementation**: 
    + does it affect component boundaries, intefaces or system decompositions? -> Design
    + does it affect code organization *within* an already-defined component? -> Implementation
- **Organizational/Process versus Constraint":
    + is it a team or process agreement about how to work? -> Organizational/Process
    + is it an imposed rule with no team-related discretion? -> Constraint

## Confidence score:
- *High (0.8-1.0):* Clear match with a predominant category and passes all tests.
- *Medium (0.6-0.79):* Generally fits but with some ambiguity.
- *Low (0.3-0.59):* Significant ambiguity; can fit multiple categories.
"""

ZIMMERMANN_FRAMEWORK_V1 = """You are a software architecture expert. Your task is to analyze Architectural Decision Records (ADRs) and classify them according to the categories provided below.

## Categories:
* Design: This decision concerns the logical organization, structure, and decomposition of the system. Related to patterns, components, layering, interfaces, data modeling.
* Technology: This decision concerns the selection of technologies, platforms, frameworks, libraries, or standards.
* Infrastructure: This decision involves the deployment environment, hosting, runtime platforms, networking, and hardware concerns.
* Organizational/Process: This decision concerns team structures, roles, responsibilities, workflows, and processes that affect architecture.
* Constraint: It refers to mandatory conditions from the business, regulations, or existing systems that limit architectural choices.
* Quality Attribute: This decision explicitly targets system qualities like performance, security, availability, etc. These are decisions made primarily to meet a non-functional requirement.
* Crosscutting Concerns: This refers to decisions that impact multiple parts of the system simultaneously, often aspects like logging, monitoring, security mechanisms.
* Implementation: This decision affects internal code structure, patterns at the class or method level, or maintainability mechanisms, but are not architectural in scope.
* Other: Use this only if the decision clearly does not fit any previous category (including the new ones). This should be rare and typically flagged for human review.

## Guidelines:
* Use all information available, base your classification on what is available, noting uncertainty if needed.
* If uncertain about classification, assign the most likely category and reflect that uncertainty in your confidence scores.
* Always explain your reasoning briefly but clearly.
"""

ZIMMERMANN_FRAMEWORK_WITH_EXAMPLES_V1 = """You are a software architecture expert. Your task is to analyze Architectural Decision Records (ADRs) and classify them according to the categories provided below.

## Categories:
* Design: This decision concerns the logical organization, structure, and decomposition of the system. Related to patterns, components, layering, interfaces, data modeling.
  - E.g., "We apply the Model-View-Controller pattern for the UI."
  - E.g., "Services must be stateless to support scalability."
* Technology: This decision concerns the selection of technologies, platforms, frameworks, libraries, or standards.
  - E.g., "We use Kubernetes for container orchestration."
  - E.g., "The database must be PostgreSQL 14."
* Infrastructure: This decision involves the deployment environment, hosting, runtime platforms, networking, and hardware concerns.
  - E.g., "Production servers must be hosted on AWS EC2 instances."
  - E.g., "Services will communicate over a secured VPN."
* Organizational/Process: This decision concerns team structures, roles, responsibilities, workflows, and processes that affect architecture.
  - E.g., "All changes must be approved by the Architecture Review Board."
  - E.g., "Scrum is adopted for project management."
* Constraint: It refers to mandatory conditions from the business, regulations, or existing systems that limit architectural choices.
  - E.g., "Compliance with GDPR is required."
  - E.g., "We must reuse the legacy CRM system without modifications."
* Quality Attribute: This decision explicitly targets system qualities like performance, security, availability, etc. These are decisions made primarily to meet a non-functional requirement.
  - E.g., "All APIs must respond within 200ms under normal load."
  - E.g., "System must be highly available with 99.99% uptime."
* Crosscutting Concerns: This refers to decisions that impact multiple parts of the system simultaneously, often aspects like logging, monitoring, security mechanisms.
  - E.g., "All services must include structured logging in JSON."
  - E.g., "Authentication must be centralized via OAuth2."
* Implementation: This decision affects internal code structure, patterns at the class or method level, or maintainability mechanisms, but are not architectural in scope.
  - E.g., "We apply the Repository pattern to separate data access from business logic."
  - E.g., "Service classes should use constructor-based dependency injection."
  - E.g., "Each domain object implements a to_dict() method for JSON serialization."
* Other: Use this only if the decision clearly does not fit any previous category (including the new ones). This should be rare and typically flagged for human review.
  - E.g., "This ADR exists only to record that we had a meeting on this topic."
  - E.g., "Decision withdrawn – no action taken."
  - E.g., "We document this placeholder for a future decision."

## Guidelines:
* Use all information available, base your classification on what is available, noting uncertainty if needed.
* If uncertain about classification, assign the most likely category and reflect that uncertainty in your confidence scores.
* Always explain your reasoning briefly but clearly.
"""

# -------------------------------------------------------------------------------------------------

def get_classification_prompts(include_examples: bool = True) -> dict[str, str]:
    if not include_examples:
        return {
            "kruchten": KRUCHTEN_FRAMEWORK_V2,
            "quality_attributes": QUALITY_ATTRIBUTES_FRAMEWORK_V2,
            "zimmermann": ZIMMERMANN_FRAMEWORK_V2
        }
    else:
        return {
            "kruchten": KRUCHTEN_FRAMEWORK_WITH_EXAMPLES_V2,
            "quality_attributes": QUALITY_ATTRIBUTES_FRAMEWORK_WITH_EXAMPLES_V2,
            "zimmermann": ZIMMERMANN_FRAMEWORK_WITH_EXAMPLES_V2
        }

# -------------------------------------------------------------------------------------------------

CONSISTENCY_PROMPT_ALL_SECTIONS = """
## Instructions
For each MADR section_name (Status, Context, Decision, Consequences, Decision Drivers, Considered Options), return the following information:
* Presence: Is there a clearly labeled heading for this section in the ADR? (Yes/No) Only answer "Yes" if the ADR includes a heading specifically dedicated to this section.
* Content Quality: If present, is the section sufficiently filled with meaningful content? (Yes/No)
* Purpose Consistency: Does the content only fulfill the intended purpose of this section, without overlapping with the role of any other section? (Yes/Partial/No) Check if the section includes material that clearly belongs to a different section (e.g., analysis of options in the Context section). If so, set purpose_consistency = Partial. 
* Short Justification: Briefly explain your reasoning if the section is missing or misused (i.e., content is insufficient or off-purpose). 

Assume the following expected purposes for each section:
  * Context. Describes the background, system state, problem, or motivation. It must not include detailed comparisons between solutions, rationales, or final decisions—those belong in "Considered Options" or "Decision". If present, mark purpose_consistency = No. 
      Includes: technical constraints, stakeholder needs, project circumstances, or related issues.
  * Decision. Clearly and explicitly states the final choice that was made in response to the context. This is the core of the ADR and should be unambiguous.
      Includes: selected approach, accepted alternative, or implemented design.
  * Consequences. Explains the results, implications, trade-offs, and expected impact of the decision—both positive and negative. Should address what follows from the decision in terms of system behavior, future maintenance, or risks.
      Includes: technical debt, performance effects, maintainability implications, limitations.
  * Decision Drivers. Lists the main criteria, goals, or forces that shaped the decision-making process. Should clarify what mattered most when choosing between options.
      Includes: performance, cost, simplicity, compatibility, regulatory compliance.
  * Considered Options. Enumerates alternative approaches or solutions that were evaluated and explains why they were not chosen. Should demonstrate that the decision was made after a comparison of viable options.
      Includes: at least two alternatives, with brief pros and cons or rejection justifications.

## Important guidelines:
* Use all available information: Base your assessment on the actual content of the ADR. If the section is ambiguous, incomplete, or poorly written, note this in your justification.
* Assume minimal context: Only rely on the information within the section. Do not infer unstated intentions or decisions.
* Favor clarity over assumption: If a section appears present but vague or off-topic, mark it as present but inconsistent with its intended purpose.
* Be conservative in evaluation: If a section lacks substance, even if labeled, mark its content quality as "No".
* Explain briefly but precisely: Justifications should directly reference what is (or isn't) in the text and why that supports your judgment.
* Consistency matters: A section with off-topic content should be flagged under “purpose_consistency” even if it is formally present and sufficiently long.
* Treat examples cautiously: If an ADR includes a sample or placeholder (e.g., “This is how you should fill out the context section”), treat it as misuse unless clearly replaced with project-specific information.
* Strict Scope Rule: If a section includes substantial content that belongs to another section (e.g., "Context" contains detailed comparisons between alternatives, which belongs in "Considered Options"), you must mark purpose_consistency = No. Even if the content is well-written or informative, it fails to fulfill the section's specific role and should be penalized. Do not give it a perfect score or mark it as consistent.
* Even if useful information appears under the wrong heading, it must not be marked as "purpose_consistent". Penalize any section that fulfills another section's role. Do not assume intent based on quality—judge only structure and alignment.

## ADR Input
{adr_input}
"""


CONSISTENCY_PROMPT_BY_SECTION = """
Your purpose is to analyze the MADR section "{section_name}".
Assume the following expected purpose of the "{section_name}" section:
{section_purpose}

## Instructions
For the MADR section "{section_name}", return the following information:
* Presence: Only answer "Yes" if the ADR includes a heading that exactly matches the expected section title (e.g., "{section_name}"). Otherwise, answer "No".
* Alternate Title: If the content clearly fulfilling the intended purpose of this section appears under a different heading, return that heading or those headings exactly as written in the ADR, as a list.
    * If multiple headings serve this role, list them all.
    * If no such alternate heading exists, return an empty list.
    * Example: If {section_name} appears under "Context", return ["Context"].
    * Example: If the content of {section_name} is scattered across "Decision" and "Context", use: ["Decision", "Context"]

* Content Quality: If the section (or its alternate) is present, does it include meaningful, project-specific content?
    * Return "Yes" if it contains actual decisions or reasoning, not just placeholders or vague statements.
    * Return "No" if the content is generic, minimal, empty, or only an example.

* Purpose Consistency: Does the content fulfill only the intended purpose of this section, without overlapping with the roles of other sections?
    * "Yes": Clear, well-scoped content.
    * "Partial": Some overlap with another section.
    * "No": Content mostly belongs elsewhere or completely fails to fulfill its purpose.

* Justification: A brief but precise explanation of your assessment. Point out:
    * If the section is missing or mislabeled
    * If content is vague, off-topic, or misplaced
    * Why the content does or doesn't fulfill the section's intended role

## Chain-of-Thought Checklist (Follow these reasoning steps)
1. Is a section with the expected title present? (Set presence)
2. If not, is the content fulfilling this role found under another heading? (Set alternate_title)
3. Is the content substantial and project-specific? (Set content_quality)
4. Is the content dedicated to this purpose and not another? (Set purpose_consistency)
5. Explain briefly why your assessments above (1 to 4) in your justification.

## Important guidelines:
* Use all available information: Base your assessment on what’s actually in the ADR.
* Assume minimal context: Do not infer intentions; rely only on text.
* Favor clarity over assumption: Label vague or misplaced sections accordingly.
* Be conservative in evaluation: If the section lacks substance or structure, mark it as "No" or "Partial".
* Consistency matters: Penalize sections that duplicate or overlap with others.
* Treat examples cautiously: Placeholder/sample content should be marked as misuse unless replaced with real content.
* Strict Scope Rule: Even if content is well-written, if it appears under the wrong heading (e.g., "Context" instead of "Considered Options" or "Context" instead of "Decision Drivers"), you must:
    * Set presence = "No"
    * Include the heading under alternate_title
    * Set purpose_consistency = "Partial" or "No"

## ADR Input
{adr_input}
"""

FULL_CONSISTENCY_OVER_EXTRACTED_ADR = """
Your an expert software architect that knows about Architecture Decision Records (ADRs)
Your task is to check the ADR below and assess its adherence to the sections of the MADR template based on the following JSON format: 

For each section, analyze: 
- if the section is present in the ADR under the right title/subtitle, and 
- if the section contents are present somewhere in the ADR text.  

Note:
- A section can have its content present but lack a proper heading (e.g., 'Decision' content is present but not under a clear heading).
- If such misalignments exist (title vs. content location), describe them in your assessment.

Your adherence score, between 0.0 (lack of alignment) and 1.0 (almost perfect alignment), should be calculated based on the presence and degree of alignment of each section. 
Please make your assessment of each section before giving the adherence score.

For the assessment, use a string list of bullets to enumerate your individual analysis of each template section.

ADR text: "{input_text}"
"""

# -------------------------------------------------------------------------------------------------

def get_adr_sections_metadata() -> dict[str, str]:
  sections = {}
  sections['Context'] = 'Describes the background, system state, problem, or motivation. It must not include detailed comparisons between solutions, rationales, or final decisions—those belong in "Considered Options" or "Decision". If present, mark purpose_consistency = No. Includes: technical constraints, stakeholder needs, project circumstances, or related issues.'
  sections['Decision'] = 'Clearly and explicitly states the final choice that was made in response to the context. This is the core of the ADR and should be unambiguous. Includes: selected approach, accepted alternative, or implemented design.'
  sections['Consequences'] = 'Explains the results, implications, trade-offs, and expected impact of the decision—both positive and negative. Should address what follows from the decision in terms of system behavior, future maintenance, or risks. Includes: technical debt, performance effects, maintainability implications, limitations.'
  sections['Decision Drivers'] = 'Lists the main criteria, goals, or forces that shaped the decision-making process. Should clarify what mattered most when choosing between options. Includes: performance, cost, simplicity, compatibility, regulatory compliance.'
  sections['Considered Options'] = 'Enumerates alternative approaches or solutions that were evaluated and explains why they were not chosen. Should demonstrate that the decision was made after a comparison of viable options. Includes: at least two alternatives, with brief pros and cons or rejection justifications.'

  return sections

# -------------------------------------------------------------------------------------------------

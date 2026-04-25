class PatientInput {
  const PatientInput({
    required this.age,
    required this.sex,
    required this.oldpeak,
    required this.chestPain,
    required this.restingBpFinal,
    required this.cholFinal,
    required this.maxHrFinal,
    required this.fastingBs,
    required this.restingEcg,
    required this.exerciseAngina,
    required this.stSlope,
  });

  final double age;
  final String sex;
  final double oldpeak;
  final String chestPain;
  final double restingBpFinal;
  final double cholFinal;
  final double maxHrFinal;
  final String fastingBs;
  final String restingEcg;
  final String exerciseAngina;
  final String stSlope;

  Map<String, dynamic> toJson() {
    return {
      'age': age,
      'sex': sex,
      'oldpeak': oldpeak,
      'chest_pain': chestPain,
      'restingbp_final': restingBpFinal,
      'chol_final': cholFinal,
      'maxhr_final': maxHrFinal,
      'fasting_bs': fastingBs,
      'resting_ecg': restingEcg,
      'exercise_angina': exerciseAngina,
      'st_slope': stSlope,
    };
  }

  factory PatientInput.fromJson(Map<String, dynamic> json) {
    return PatientInput(
      age: (json['age'] as num).toDouble(),
      sex: json['sex'] as String,
      oldpeak: (json['oldpeak'] as num).toDouble(),
      chestPain: json['chest_pain'] as String,
      restingBpFinal: (json['restingbp_final'] as num).toDouble(),
      cholFinal: (json['chol_final'] as num).toDouble(),
      maxHrFinal: (json['maxhr_final'] as num).toDouble(),
      fastingBs: json['fasting_bs'] as String,
      restingEcg: json['resting_ecg'] as String,
      exerciseAngina: json['exercise_angina'] as String,
      stSlope: json['st_slope'] as String,
    );
  }

  PatientInput copyWith({
    double? age,
    String? sex,
    double? oldpeak,
    String? chestPain,
    double? restingBpFinal,
    double? cholFinal,
    double? maxHrFinal,
    String? fastingBs,
    String? restingEcg,
    String? exerciseAngina,
    String? stSlope,
  }) {
    return PatientInput(
      age: age ?? this.age,
      sex: sex ?? this.sex,
      oldpeak: oldpeak ?? this.oldpeak,
      chestPain: chestPain ?? this.chestPain,
      restingBpFinal: restingBpFinal ?? this.restingBpFinal,
      cholFinal: cholFinal ?? this.cholFinal,
      maxHrFinal: maxHrFinal ?? this.maxHrFinal,
      fastingBs: fastingBs ?? this.fastingBs,
      restingEcg: restingEcg ?? this.restingEcg,
      exerciseAngina: exerciseAngina ?? this.exerciseAngina,
      stSlope: stSlope ?? this.stSlope,
    );
  }
}

const defaultPatientInput = PatientInput(
  age: 55,
  sex: 'Male',
  oldpeak: 2.0,
  chestPain: 'Atypical Angina',
  restingBpFinal: 140,
  cholFinal: 250,
  maxHrFinal: 150,
  fastingBs: 'No',
  restingEcg: 'Normal',
  exerciseAngina: 'No',
  stSlope: 'Flat',
);

const sampleHighRiskPatient = PatientInput(
  age: 65,
  sex: 'Male',
  oldpeak: 2.5,
  chestPain: 'Asymptomatic',
  restingBpFinal: 160,
  cholFinal: 300,
  maxHrFinal: 130,
  fastingBs: 'Yes',
  restingEcg: 'ST-T Abnormality',
  exerciseAngina: 'Yes',
  stSlope: 'Flat',
);
